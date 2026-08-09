// 全局主题共享脚本：深色模式跨页面持久化
// 在 <head> 中同步引入，加载即应用已保存主题，避免闪烁
(function () {
    var root = document.documentElement;
    if (localStorage.getItem('chatTheme') === 'dark') {
        root.classList.add('dark-theme');
    }

    document.addEventListener('DOMContentLoaded', function () {
        var btn = document.getElementById('themeToggle');
        if (!btn) return;
        // 同步按钮图标
        btn.textContent = root.classList.contains('dark-theme') ? '☀️' : '🌙';
        btn.addEventListener('click', function () {
            var isDark = root.classList.toggle('dark-theme');
            localStorage.setItem('chatTheme', isDark ? 'dark' : 'light');
            btn.textContent = isDark ? '☀️' : '🌙';
        });
    });
})();
