function updateThemeColor(theme) {
    const themeColor = theme === 'dark' ? '#1a1a1a' : '#ffffff';
    const themeColorMeta = document.querySelector('meta[name="theme-color"]');
    if (themeColorMeta) {
        themeColorMeta.setAttribute('content', themeColor);
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeColor(theme);
}

class TypingAnimation {
    constructor() {
        this.mainTitle = document.getElementById('mainTitle');
        this.logoIcon = document.querySelector('.logo-icon');
        this.currentText = 'kristiam.xyz';
        this.isAnimating = false;
    }

    async start() {
        if (this.isAnimating || !this.mainTitle) return;
        this.isAnimating = true;

        if (this.logoIcon) {
            this.logoIcon.style.opacity = '1';
            this.logoIcon.style.transform = 'rotate(0deg)';
        }

        await this.wait(500);
        if (this.logoIcon) {
            this.logoIcon.style.transition = 'opacity 0.2s ease';
            this.logoIcon.style.opacity = '0';
        }

        this.mainTitle.style.transition = 'margin-left 1s ease';
        this.mainTitle.style.marginLeft = '-2rem';

        await this.wait(500);
        await this.deleteCharacters(5);
        await this.wait(1000);
        await this.typeText('n');
        await this.typeText(' ristic');

        if (this.logoIcon) {
            await this.revealAndSpinLogo();
        }

        this.isAnimating = false;
    }

    async deleteCharacters(count) {
        for (let i = 0; i < count; i++) {
            await this.wait(300);
            this.currentText = this.currentText.slice(0, -1);
            this.updateDisplay();
        }
    }

    async typeText(text) {
        for (const char of text) {
            await this.wait(250);
            this.currentText += char;
            this.updateDisplay();
        }
    }

    async revealAndSpinLogo() {
        this.logoIcon.style.transition = 'opacity 0.2s ease, transform 2s ease';
        this.logoIcon.style.opacity = '1';
        this.logoIcon.style.transform = 'rotate(360deg)';
        this.mainTitle.style.transition = 'margin-left 1s ease';
        this.mainTitle.style.marginLeft = '0';
        await this.wait(2000);
    }

    updateDisplay() {
        this.mainTitle.textContent = this.currentText;
    }

    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

function initThemeSwitcher() {
    applyTheme(localStorage.getItem('theme') || 'dark');

    const themeToggle = document.querySelector('.theme-toggle');
    if (!themeToggle) return;

    themeToggle.addEventListener('click', (e) => {
        e.preventDefault();
        const current = document.documentElement.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
    });
}

function setupMenuHover() {
    const menuLinks = document.querySelectorAll('.menu-link');

    menuLinks.forEach(link => {
        link.addEventListener('mouseenter', () => {
            menuLinks.forEach(l => {
                l.style.fontSize = '1rem';
                l.style.fontWeight = '400';
            });
            link.style.fontSize = '1.2rem';
            link.style.fontWeight = '500';
        });

        link.addEventListener('mouseleave', () => {
            menuLinks.forEach(l => {
                const active = l.classList.contains('active');
                l.style.fontSize = active ? '1.2rem' : '1rem';
                l.style.fontWeight = active ? '500' : '400';
            });
        });
    });
}

function setupCategoryFilters() {
    const filters = document.querySelectorAll('.category-filter');
    const postsContainer = document.getElementById('posts-container');
    if (!filters.length || !postsContainer) return;

    filters.forEach(filter => {
        filter.addEventListener('click', (e) => {
            e.preventDefault();
            filters.forEach(f => f.classList.remove('active'));
            filter.classList.add('active');

            const category = filter.getAttribute('data-category');
            postsContainer.querySelectorAll('.post-item').forEach(item => {
                const cats = (item.getAttribute('data-categories') || '').split(/\s+/);
                item.style.display = category === 'all' || cats.includes(category) ? '' : 'none';
            });
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initThemeSwitcher();
    setupMenuHover();
    setupCategoryFilters();

    if (document.getElementById('mainTitle')) {
        setTimeout(() => new TypingAnimation().start(), 1000);
    }
});
