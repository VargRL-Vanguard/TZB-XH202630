"""
3 项硬指标计算器（**挑战杯夺奖核心**）。

函数签名严格按任务清单 S-01 验收标准，不允许改动。
所有函数返回 [0, 1] 浮点数。
"""
import re
from typing import Iterable

# ---------------- 工具函数 ----------------

# 用 raw string + 双反斜杠转义，避免 SyntaxWarning
# 字符类内部：[ ] \ - 需要转义，其他字符在中文字符类里直接用即可
_PUNCT_RE = re.compile(
    r"[\s，。！？、；：\"'《》（）()\[\]【】\-—,.!?;:]+"
)


def _split_sentences(text: str) -> list[str]:
    """把文本切成句子（按中英文标点）。"""
    if not text:
        return []
    # 先按段落切，再按句号切
    parts: list[str] = []
    for para in re.split(r"\n+", text):
        if not para.strip():
            continue
        for s in re.split(r"(?<=[。！？!?\.])\s*", para):
            s = s.strip()
            if s:
                parts.append(s)
    return parts


def _normalize(text: str) -> str:
    """统一小写、去标点、去多余空白。"""
    return _PUNCT_RE.sub("", text).lower().strip()


def _word_set(text: str) -> set[str]:
    """把文本切成"词集合"（中文按字、英文按 word）。"""
    norm = _normalize(text)
    if not norm:
        return set()
    # 中文按字 + 英文按 word
    tokens: list[str] = []
    buf: list[str] = []
    for ch in norm:
        if "\u4e00" <= ch <= "\u9fff":
            # 中文：flush buffer, push 单字
            if buf:
                tokens.append("".join(buf))
                buf = []
            tokens.append(ch)
        else:
            buf.append(ch)
    if buf:
        tokens.append("".join(buf))
    return {t for t in tokens if t}


# ---------------- 1. 幻觉率 ----------------

def calc_hallucination_rate(generated: str, ground_truth: Iterable[str]) -> float:
    """
    幻觉率 = 资源中"未在 ground_truth 切片里出现"的内容占比。

    算法（关键词匹配 + 滑窗）：
    1. 把 generated 切成句子
    2. 把所有 ground_truth 切片合并成一个"允许的词集合 + 原文"
    3. 对每句：检查它是否被任一 ground_truth 引用（句子里的关键词在 ground_truth 里出现）
    4. 幻觉率 = 不被引用的句子字数 / 总字数

    :param generated: 生成的资源文本（str）
    :param ground_truth: 引用的知识库切片列表（list[str]）
    :return: 浮点数 [0, 1]，越小越好，< 0.05 才达标
    """
    if not generated:
        return 0.0

    # 1. 准备 ground_truth 的"允许词集合" + 原文
    truth_list = list(ground_truth) if ground_truth else []
    truth_text = "\n".join(truth_list)
    truth_words = _word_set(truth_text)

    if not truth_words:
        # 没有任何 ground_truth → 全部算幻觉
        return 1.0

    # 2. 切句
    sentences = _split_sentences(generated)
    if not sentences:
        return 0.0

    # 3. 对每句检查
    total_chars = 0
    hallucinated_chars = 0
    MIN_OVERLAP = 0.30  # 句子与 truth 的词重合度阈值

    for sent in sentences:
        sent_words = _word_set(sent)
        sent_len = len(sent)
        total_chars += sent_len

        if not sent_words:
            # 纯标点，不算幻觉
            continue

        overlap = len(sent_words & truth_words)
        overlap_ratio = overlap / len(sent_words)

        if overlap_ratio < MIN_OVERLAP:
            # 这句话里的词在 truth 里出现太少 → 视为幻觉
            hallucinated_chars += sent_len

    if total_chars == 0:
        return 0.0
    return min(1.0, hallucinated_chars / total_chars)


# ---------------- 2. 画像-难度适配准确率 ----------------

def calc_match_accuracy(
    profile: dict,
    resource_difficulty: int,
    expected_difficulty_key: str = "recommendedDifficulty",
) -> float:
    """
    画像-难度适配准确率。

    算法（完全相等）：
    1. 从 profile 取 expected[expected_difficulty_key]
    2. 与 resource_difficulty 比较
    3. 相等 → 1.0；不等 → 0.0
    4. 多组 profile 时由调用方聚合（这里返回单组 0/1）

    :param profile: 学生画像 dict（含 "expected" 子 dict）
    :param resource_difficulty: 资源推荐难度（1-5 整数）
    :param expected_difficulty_key: expected 里的字段名
    :return: 0.0（不匹配）或 1.0（匹配）；用于聚合时累加后除以总数
    """
    if not isinstance(profile, dict):
        return 0.0

    expected = profile.get("expected", {})
    if not isinstance(expected, dict):
        return 0.0

    expected_difficulty = expected.get(expected_difficulty_key)
    if expected_difficulty is None:
        return 0.0

    # 都转 int 比较（容忍 "3" / 3.0 / 3）
    try:
        expected_int = int(expected_difficulty)
        resource_int = int(resource_difficulty)
    except (TypeError, ValueError):
        return 0.0

    return 1.0 if expected_int == resource_int else 0.0


# ---------------- 3. 核心知识点覆盖率 ----------------

def calc_coverage(generated: dict | list, required_kps: list[str]) -> float:
    """
    核心知识点覆盖率。

    算法（kp_tags 字段对比）：
    1. 从 generated 里拿 kp_coverage 列表
       - 如果 generated 是 dict：取 generated.get("kp_coverage", [])
       - 如果 generated 是 list：直接视为 kp_coverage
    2. 与 required_kps 求交集
    3. 覆盖率 = |交集| / |required_kps|

    :param generated: 资源（dict 含 kp_coverage 字段）或 kp 列表
    :param required_kps: 必需的知识点 ID 列表
    :return: 浮点数 [0, 1]，越大越好，≥ 0.90 才达标
    """
    if not required_kps:
        # 没有必需 kp → 视为 100% 覆盖
        return 1.0

    # 1. 提取 covered 集合
    if isinstance(generated, dict):
        covered = generated.get("kp_coverage", []) or []
    elif isinstance(generated, list):
        covered = generated
    else:
        covered = []

    # 2. 统一成 set
    try:
        covered_set = set(str(k) for k in covered)
        required_set = set(str(k) for k in required_kps)
    except TypeError:
        return 0.0

    if not required_set:
        return 1.0

    # 3. 计算覆盖率
    intersection = covered_set & required_set
    return len(intersection) / len(required_set)
