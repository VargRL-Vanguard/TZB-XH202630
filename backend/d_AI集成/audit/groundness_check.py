"""
幻觉率校验（D-06 ⭐ 夺奖专项）。

算法：
  1. 把 content 拆句
  2. 每句调 B 的 list_kb_chunks_by_kp 检索知识库
  3. 用 A 的 calc_hallucination_rate 计算幻觉率
  4. 相似度 < 0.5 的句子标记为幻觉

返回：{hallucinationRate, hallucinatedSentences[], totalSentences}
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional

from backend.公共.logger import get_logger
from backend.公共.metrics import calc_hallucination_rate

log = get_logger(__name__)

# 幻觉判定阈值：句子与知识库切片的词重合度低于此值视为幻觉
HALLUCINATION_THRESHOLD = 0.5

# KB 检索超时（秒）
_KB_TIMEOUT = 5.0


def _split_sentences(text: str) -> list[str]:
    """把文本切成句子（按中英文标点）。"""
    if not text:
        return []
    parts: list[str] = []
    for para in re.split(r"\n+", text):
        para = para.strip()
        if not para:
            continue
        for s in re.split(r"(?<=[。！？!?\.])\s*", para):
            s = s.strip()
            if s:
                parts.append(s)
    return parts


def _normalize(text: str) -> str:
    """统一小写、去标点、去多余空白。"""
    _PUNCT_RE = re.compile(
        r"[\s，。！？、；：\"'《》（）()\[\]【】\-—,.!?;:]+"
    )
    return _PUNCT_RE.sub("", text).lower().strip()


def _word_set(text: str) -> set[str]:
    """把文本切成词集合。"""
    norm = _normalize(text)
    if not norm:
        return set()
    tokens: list[str] = []
    buf: list[str] = []
    for ch in norm:
        if "\u4e00" <= ch <= "\u9fff":
            if buf:
                tokens.append("".join(buf))
                buf = []
            tokens.append(ch)
        else:
            buf.append(ch)
    if buf:
        tokens.append("".join(buf))
    return {t for t in tokens if t}


def _sentence_similarity(sentence: str, chunk_texts: list[str]) -> float:
    """
    计算句子与知识库切片集合的最大相似度（词重合度）。
    返回 [0, 1]。
    """
    if not chunk_texts:
        return 0.0
    sent_words = _word_set(sentence)
    if not sent_words:
        return 1.0  # 纯标点不算幻觉

    best = 0.0
    for ct in chunk_texts:
        chunk_words = _word_set(ct)
        if not chunk_words:
            continue
        overlap = len(sent_words & chunk_words)
        sim = overlap / len(sent_words)
        if sim > best:
            best = sim
    return best


async def _retrieve_kb_for_sentence(
    sentence: str,
    kp_ids: list[str],
    top_k: int = 5,
) -> list[str]:
    """
    对给定的句子，按 kp_ids 检索知识库，返回所有切片文本列表。
    失败时降级返回空列表。
    """
    all_chunk_texts: list[str] = []
    try:
        from backend.b_学情数据.kb import list_kb_chunks_by_kp

        for kp_id in kp_ids[:5]:  # 最多检索 5 个 kp，避免过慢
            try:
                chunks = await asyncio.wait_for(
                    list_kb_chunks_by_kp(kp_id, limit=top_k),
                    timeout=_KB_TIMEOUT,
                )
                for c in chunks:
                    text = c.get("content") or c.get("text") or ""
                    if text:
                        all_chunk_texts.append(text)
            except asyncio.TimeoutError:
                log.warning(f"KB检索超时 kp={kp_id}")
            except Exception as e:
                log.warning(f"KB检索失败 kp={kp_id}: {e}")
    except ImportError:
        log.warning("B 区知识库不可用，幻觉率校验降级为全部通过")
    except Exception as e:
        log.warning(f"KB检索异常: {e}")

    return all_chunk_texts


async def check_hallucination(
    content: str,
    kp_ids: list[str],
) -> dict:
    """
    幻觉率校验主函数。

    :param content: 被审核的内容文本
    :param kp_ids: 内容涉及的知识点 ID 列表
    :return: {
        hallucinationRate: float,      # 幻觉率 [0,1]
        hallucinatedSentences: list,   # 被标记为幻觉的句子
        totalSentences: int,           # 总句子数
        sentenceDetails: list[dict],   # 每句的相似度详情
    }
    """
    sentences = _split_sentences(content)
    if not sentences:
        return {
            "hallucinationRate": 0.0,
            "hallucinatedSentences": [],
            "totalSentences": 0,
            "sentenceDetails": [],
        }

    # 一次性检索所有 kp 的切片（避免逐句检索，提高效率）
    all_chunk_texts = await _retrieve_kb_for_sentence("", kp_ids, top_k=10)

    hallucinated: list[str] = []
    details: list[dict] = []

    for sent in sentences:
        sim = _sentence_similarity(sent, all_chunk_texts)
        is_hallucination = sim < HALLUCINATION_THRESHOLD
        details.append({
            "sentence": sent[:100],
            "similarity": round(sim, 4),
            "isHallucination": is_hallucination,
        })
        if is_hallucination:
            hallucinated.append(sent)

    total = len(sentences)
    hr = len(hallucinated) / total if total > 0 else 0.0

    # 同时用 A 区标准函数交叉验证
    try:
        hr_standard = calc_hallucination_rate(content, all_chunk_texts)
        # 取两者中较大值作为保守估计
        hr = max(hr, hr_standard)
    except Exception as e:
        log.warning(f"calc_hallucination_rate 交叉验证失败: {e}")

    return {
        "hallucinationRate": round(min(1.0, hr), 4),
        "hallucinatedSentences": [s[:100] for s in hallucinated],
        "totalSentences": total,
        "sentenceDetails": details,
    }