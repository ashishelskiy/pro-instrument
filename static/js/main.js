// Утилита для переключения изображений
function switchImage(element) {
    const mainImage = document.querySelector('.product-image');
    if (mainImage) {
        mainImage.src = element.src;
    }
}

// Фильтры на странице категорий
document.addEventListener('DOMContentLoaded', function() {
    // Автоматическая отправка формы фильтра при изменении
    const filterForm = document.querySelector('.filter-form');
    if (filterForm) {
        const inputs = filterForm.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                filterForm.submit();
            });
        });
    }

    // Анимация для карточек товаров
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.classList.add('product-card');
    });
});

// Уведомления
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.querySelector('.container').prepend(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}