// static/js/main.js

// =============================================================
// ПОЛИФИЛЛ ДЛЯ CSS.escape() (если браузер не поддерживает)
// =============================================================

if (!CSS || !CSS.escape) {
    CSS = CSS || {};
    CSS.escape = function(value) {
        return String(value).replace(/([^a-zA-Z0-9\-_])/g, '\\$1');
    };
}

// =============================================================
// MEGA-MENU
// =============================================================

function initCatalogMenu() {
    const catalogToggle = document.getElementById('catalogToggle');
    const catalogMenu = document.getElementById('catalogMenu');
    const headerCatalog = document.querySelector('.header-catalog');
    const sectionItems = document.querySelectorAll('.catalog-menu__section-item');
    const subsectionsContainer = document.getElementById('subsectionsContainer');
    const catalogInner = document.querySelector('.catalog-menu__inner');
    const allGroups = document.querySelectorAll('.catalog-menu__subsections-group');

    if (!catalogToggle || !catalogMenu) {
        console.warn('Элементы мегаменю не найдены');
        return;
    }

    let isMobile = window.innerWidth <= 768;
    let hoverTimeout = null;
    let activeCategory = null;

    window.addEventListener('resize', function() {
        isMobile = window.innerWidth <= 768;
    });

    // =========================================================
    // ПОКАЗ ПОДКАТЕГОРИЙ
    // =========================================================

    function showSubsections(slug) {
        allGroups.forEach(group => {
            group.classList.remove('is-active');
        });

        const targetGroup = document.querySelector(
            `.catalog-menu__subsections-group[data-section="${CSS.escape(slug)}"]`
        );

        if (targetGroup) {
            targetGroup.classList.add('is-active');
            subsectionsContainer.classList.add('is-active');
            catalogInner.classList.add('has-subsections');
            activeCategory = slug;
        } else {
            subsectionsContainer.classList.remove('is-active');
            catalogInner.classList.remove('has-subsections');
            activeCategory = null;
        }
    }

    // =========================================================
    // ЗАКРЫТИЕ МЕНЮ
    // =========================================================

    function closeMenu() {
        catalogMenu.classList.remove('is-active');
        catalogToggle.setAttribute('aria-expanded', 'false');
        catalogMenu.setAttribute('aria-hidden', 'true');
        subsectionsContainer.classList.remove('is-active');
        catalogInner.classList.remove('has-subsections');
        allGroups.forEach(group => {
            group.classList.remove('is-active');
        });
        activeCategory = null;
        catalogToggle.focus();
    }

    // =========================================================
    // ОТКРЫТИЕ МЕНЮ
    // =========================================================

    function openMenu() {
        catalogMenu.classList.add('is-active');
        catalogToggle.setAttribute('aria-expanded', 'true');
        catalogMenu.setAttribute('aria-hidden', 'false');

        const firstWithChildren = Array.from(sectionItems).find(
            item => item.dataset.hasChildren === 'true'
        );
        if (firstWithChildren) {
            showSubsections(firstWithChildren.dataset.section);
        }
    }

    // =========================================================
    // ПЕРЕКЛЮЧЕНИЕ МЕНЮ
    // =========================================================

    function toggleMenu() {
        if (catalogMenu.classList.contains('is-active')) {
            closeMenu();
        } else {
            openMenu();
        }
    }

    // =========================================================
    // ОБРАБОТЧИКИ СОБЫТИЙ
    // =========================================================

    // Клик по кнопке
    catalogToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleMenu();
    });

    // Закрытие по Escape (только это из клавиатуры)
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && catalogMenu.classList.contains('is-active')) {
            closeMenu();
            catalogToggle.focus();
        }
    });

    // Закрытие при клике вне
    document.addEventListener('click', function(e) {
        if (!headerCatalog.contains(e.target)) {
            closeMenu();
        }
    });

    // =========================================================
    // DESKTOP: HOVER
    // =========================================================

    sectionItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            if (!isMobile && catalogMenu.classList.contains('is-active')) {
                if (hoverTimeout) {
                    clearTimeout(hoverTimeout);
                    hoverTimeout = null;
                }

                const slug = this.dataset.section;
                const hasChildren = this.dataset.hasChildren === 'true';

                if (hasChildren) {
                    hoverTimeout = setTimeout(() => {
                        showSubsections(slug);
                        hoverTimeout = null;
                    }, 120);
                } else {
                    subsectionsContainer.classList.remove('is-active');
                    catalogInner.classList.remove('has-subsections');
                    allGroups.forEach(group => {
                        group.classList.remove('is-active');
                    });
                    activeCategory = null;
                }
            }
        });

        item.addEventListener('mouseleave', function() {
            if (hoverTimeout) {
                clearTimeout(hoverTimeout);
                hoverTimeout = null;
            }
        });

        // =====================================================
        // MOBILE: CLICK
        // =====================================================

        item.addEventListener('click', function(e) {
            if (!isMobile) return;

            const slug = this.dataset.section;
            const hasChildren = this.dataset.hasChildren === 'true';

            if (!hasChildren) return;

            const isSameCategory = activeCategory === slug;

            if (isSameCategory) {
                return;
            }

            e.preventDefault();
            showSubsections(slug);
        });
    });

    console.log('✅ Мегаменю инициализировано');
}

// =============================================================
// ФИЛЬТРЫ
// =============================================================

function initFilters() {
    const filterForm = document.querySelector('.filter-form');
    if (!filterForm) return;

    const inputs = filterForm.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('change', function() {
            filterForm.submit();
        });
    });
}

// =============================================================
// КАРТОЧКИ ТОВАРОВ
// =============================================================

function initProductCards() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.classList.add('product-card');
    });
}

// =============================================================
// ПЕРЕКЛЮЧЕНИЕ ИЗОБРАЖЕНИЯ ТОВАРА
// =============================================================

function switchImage(element) {
    const mainImage = document.querySelector('.product-image');
    if (mainImage) {
        mainImage.src = element.src;
    }
}

// =============================================================
// УВЕДОМЛЕНИЯ
// =============================================================

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    const container = document.querySelector('main .container') || document.querySelector('.container');
    if (!container) return;

    container.prepend(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// =============================================================
// INIT
// =============================================================

document.addEventListener('DOMContentLoaded', function() {
    initCatalogMenu();
    initFilters();
    initProductCards();
});

// static/js/main.js

// =============================================================
// САЙДБАР-МЕНЮ (раскрытие подкатегорий)
// =============================================================

document.addEventListener('DOMContentLoaded', function() {
    const sidebarItems = document.querySelectorAll('.sidebar-catalog__item.has-children');

    sidebarItems.forEach(item => {
        const link = item.querySelector('.sidebar-catalog__link');

        link.addEventListener('click', function(e) {
            // Проверяем, не был ли клик по ссылке с переходом
            if (e.target.closest('.sidebar-catalog__link')) {
                e.preventDefault();
                item.classList.toggle('open');
            }
        });
    });
});