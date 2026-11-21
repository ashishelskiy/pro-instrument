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
    /*
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
    }*/

    function closeMenu() {
        if (!catalogMenu.classList.contains('is-active')) return;
        catalogMenu.classList.remove('is-active');
        catalogToggle.setAttribute('aria-expanded', 'false');
        catalogMenu.setAttribute('aria-hidden', 'true');
        subsectionsContainer.classList.remove('is-active');
        catalogInner.classList.remove('has-subsections');
        allGroups.forEach(group => {
            group.classList.remove('is-active');
        });
        activeCategory = null;
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
// САЙДБАР-МЕНЮ (раскрытие подкатегорий)
// =============================================================

function initSidebarMenu() {
    const sidebarItems = document.querySelectorAll('.sidebar-catalog__item.has-children');

    sidebarItems.forEach(item => {
        const link = item.querySelector('.sidebar-catalog__link');
        if (!link) return;

        link.addEventListener('click', function(e) {
            if (e.target.closest('.sidebar-catalog__link')) {
                e.preventDefault();
                item.classList.toggle('open');
            }
        });
    });
}

// =============================================================
// АВТОКОМПЛИТ СТРОКИ ПОИСКА
// =============================================================

function initSearchSuggest() {
    const wrapper = document.getElementById('headerSearch');
    const input = document.getElementById('headerSearchInput');
    const box = document.getElementById('searchSuggest');
    if (!wrapper || !input || !box) return;

    const form = wrapper.querySelector('form');
    const suggestUrl = wrapper.dataset.suggestUrl || '/search/suggest/';
    const searchUrl = form ? form.action : '/search/';

    let controller = null;
    let timer = null;
    let activeIndex = -1;
    let items = [];

    function hide() {
        box.hidden = true;
        box.innerHTML = '';
        input.setAttribute('aria-expanded', 'false');
        activeIndex = -1;
        items = [];
    }

    function show() {
        if (box.innerHTML.trim()) {
            box.hidden = false;
            input.setAttribute('aria-expanded', 'true');
        }
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, ch => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[ch]));
    }

    // Подсветка совпавшей части запроса
    function highlight(text, q) {
        if (!q) return escapeHtml(text);
        const safe = escapeHtml(text);
        const re = new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'ig');
        return safe.replace(re, '<mark>$1</mark>');
    }

    function render(data) {
        const parts = [];
        const cat = data.categories || [];
        const br = data.brands || [];
        const pr = data.products || [];

        if (!cat.length && !br.length && !pr.length) {
            parts.push('<div class="search-suggest__empty">Ничего не найдено</div>');
            box.innerHTML = parts.join('');
            box.hidden = false;
            input.setAttribute('aria-expanded', 'true');
            items = [];
            return;
        }

        if (cat.length) {
            parts.push('<div class="search-suggest__group-title">Категории</div>');
            cat.forEach(c => {
                parts.push(
                    `<a class="search-suggest__item" href="${c.url}">` +
                    `<i class="fas fa-folder-open"></i>` +
                    `<span class="search-suggest__item-name">${highlight(c.name, data.q)}</span>` +
                    `</a>`
                );
            });
        }

        if (br.length) {
            parts.push('<div class="search-suggest__group-title">Бренды</div>');
            br.forEach(b => {
                parts.push(
                    `<a class="search-suggest__item" href="${b.url}">` +
                    `<i class="fas fa-tag"></i>` +
                    `<span class="search-suggest__item-name">${highlight(b.name, data.q)}</span>` +
                    `</a>`
                );
            });
        }

        if (pr.length) {
            parts.push('<div class="search-suggest__group-title">Товары</div>');
            pr.forEach(p => {
                parts.push(
                    `<a class="search-suggest__item" href="${p.url}">` +
                    `<i class="fas fa-box"></i>` +
                    `<span class="search-suggest__item-name">${highlight(p.name, data.q)}</span>` +
                    `<span class="search-suggest__item-hint">${p.price} ₽</span>` +
                    `</a>`
                );
            });
        }

        // «Показать все результаты»
        const allUrl = `${searchUrl}?q=${encodeURIComponent(data.q)}`;
        parts.push('<div class="search-suggest__group-title">Ещё</div>');
        parts.push(
            `<a class="search-suggest__item" href="${allUrl}">` +
            `<i class="fas fa-search"></i>` +
            `<span class="search-suggest__item-name">Показать все результаты по «${escapeHtml(data.q)}»</span>` +
            `</a>`
        );

        box.innerHTML = parts.join('');
        box.hidden = false;
        input.setAttribute('aria-expanded', 'true');
        items = Array.from(box.querySelectorAll('.search-suggest__item'));
        activeIndex = -1;
    }

    function fetchSuggest(q) {
        if (controller) controller.abort();
        controller = new AbortController();

        fetch(`${suggestUrl}?q=${encodeURIComponent(q)}`, {
            signal: controller.signal,
            headers: {'X-Requested-With': 'XMLHttpRequest'},
        })
            .then(r => r.ok ? r.json() : Promise.reject(r))
            .then(data => {
                if (input.value.trim() !== q) return;
                render(data);
            })
            .catch(err => {
                if (err.name === 'AbortError') return;
                hide();
            });
    }

    function onInput() {
        const q = input.value.trim();
        clearTimeout(timer);
        if (q.length < 2) {
            hide();
            return;
        }
        timer = setTimeout(() => fetchSuggest(q), 200);
    }

    function moveActive(delta) {
        if (!items.length) return;
        activeIndex = (activeIndex + delta + items.length) % items.length;
        items.forEach((el, i) => el.classList.toggle('is-active', i === activeIndex));
        items[activeIndex].scrollIntoView({block: 'nearest'});
    }

    input.addEventListener('input', onInput);
    input.addEventListener('focus', show);

    input.addEventListener('keydown', e => {
        if (box.hidden) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); moveActive(1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); moveActive(-1); }
        else if (e.key === 'Enter' && activeIndex >= 0) {
            e.preventDefault();
            items[activeIndex].click();
        }
        else if (e.key === 'Escape') { hide(); }
    });

    document.addEventListener('click', e => {
        if (!wrapper.contains(e.target)) hide();
    });

    if (form) form.addEventListener('submit', hide);
}

// =============================================================
// INIT
// =============================================================

document.addEventListener('DOMContentLoaded', function() {
    initCatalogMenu();
    initFilters();
    initProductCards();
    initSidebarMenu();
    initSearchSuggest();

        if (document.querySelector('.brandsSwiper') && typeof Swiper !== 'undefined') {
        new Swiper('.brandsSwiper', {
            loop: true,
            slidesPerView: 2.3,
            slidesPerGroup: 1,
            spaceBetween: 12,
            navigation: {
                prevEl: '.brands-slider__btn--prev',
                nextEl: '.brands-slider__btn--next',
            },
            breakpoints: {
                576: { slidesPerView: 3.3 },
                768: { slidesPerView: 4 },
                992: { slidesPerView: 6 },
            },
        });
    }


});

document.addEventListener('mousedown', function(e) {
    if (e.target.closest('.brands-slider__btn, .categories-slider__btn')) {
        e.preventDefault();
    }
});