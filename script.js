function updateThemeColor(theme) {
    const themeColorMeta = document.querySelector('meta[name="theme-color"]');
    if (themeColorMeta) {
        themeColorMeta.setAttribute('content', theme === 'dark' ? '#1a1a1a' : '#ffffff');
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeColor(theme);
}

function initThemeSwitcher() {
    const theme = localStorage.getItem('theme') || 'dark';
    applyTheme(theme);

    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    toggle.setAttribute('aria-pressed', String(theme === 'dark'));
    toggle.addEventListener('click', () => {
        const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        toggle.setAttribute('aria-pressed', String(next === 'dark'));
    });
}

function setupCategoryFilters() {
    const filters = document.querySelectorAll('.category-filter');
    const postsContainer = document.getElementById('posts-container');
    if (!filters.length || !postsContainer) return;

    filters.forEach((filter) => {
        filter.addEventListener('click', (event) => {
            event.preventDefault();
            filters.forEach((item) => item.classList.remove('active'));
            filter.classList.add('active');

            const category = filter.getAttribute('data-category');
            postsContainer.querySelectorAll('.post-item').forEach((item) => {
                const categories = (item.getAttribute('data-categories') || '').split(/\s+/);
                item.hidden = category !== 'all' && !categories.includes(category);
            });
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initThemeSwitcher();
    setupCategoryFilters();
});
