// Загрузка информации о пользователе и заказах
document.addEventListener('DOMContentLoaded', async () => {
    // Ждём небольшую задержку для проверки auth
    setTimeout(async () => {
        const userId = API.getCurrentUserId();
        if (!userId) return;
        
        // Получаем полную информацию о пользователе
        const user = await API.getCurrentUser();
        if (user) {
            await initDashboard(user);
        }
    }, 100);
});

async function initDashboard(user) {
    // Отображаем информацию о пользователе
    document.getElementById('userName').textContent = user.username || user.name || 'Пользователь';
    document.getElementById('userEmail').textContent = user.email || '';
    
    // Скрываем ссылку на админку, так как ролей нет
    const adminLink = document.getElementById('adminLink');
    if (adminLink) {
        adminLink.style.display = 'none';
    }
    
    // Загружаем заказы пользователя
    await loadUserOrders(user.id);
    
    // Настройка фильтров
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const status = btn.dataset.status;
            loadUserOrders(user.id, status === 'all' ? null : status);
        });
    });
    
    // Модальное окно создания заказа
    const modal = document.getElementById('orderModal');
    const createBtn = document.getElementById('createOrderBtn');
    const closeBtn = document.querySelector('#orderModal .close');
    
    if (createBtn) {
        createBtn.onclick = () => modal.style.display = 'block';
    }
    if (closeBtn) {
        closeBtn.onclick = () => modal.style.display = 'none';
    }
    
    window.onclick = (event) => {
        if (event.target === modal) modal.style.display = 'none';
        if (event.target === document.getElementById('statusModal')) 
            document.getElementById('statusModal').style.display = 'none';
    };
    
    // Создание заказа
    const createOrderForm = document.getElementById('createOrderForm');
    if (createOrderForm) {
        createOrderForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const orderData = {
                user_id: user.id,
                product: document.getElementById('orderProduct').value,
                quantity: parseInt(document.getElementById('orderQuantity').value),
                amount: parseFloat(document.getElementById('orderAmount').value),
                status: 'pending'
            };
            
            // Валидация
            if (!orderData.product || orderData.quantity < 1 || orderData.amount <= 0) {
                showMessage('Заполните все поля корректно', 'error');
                return;
            }
            
            try {
                const result = await API.OrdersService.createOrder(orderData);
                if (result.id) {
                    modal.style.display = 'none';
                    document.getElementById('createOrderForm').reset();
                    await loadUserOrders(user.id);
                    showMessage('Заказ успешно создан!', 'success');
                } else {
                    showMessage(result.error || 'Ошибка создания заказа', 'error');
                }
            } catch (error) {
                showMessage('Ошибка создания заказа', 'error');
            }
        });
    }
    
    // Обновление статуса
    const statusForm = document.getElementById('statusForm');
    if (statusForm) {
        statusForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const orderId = document.getElementById('statusOrderId').value;
            const status = document.getElementById('orderStatus').value;
            
            try {
                const result = await API.OrdersService.updateOrderStatus(orderId, status);
                if (result.message || result.id) {
                    document.getElementById('statusModal').style.display = 'none';
                    await loadUserOrders(user.id);
                    showMessage('Статус заказа обновлён', 'success');
                }
            } catch (error) {
                showMessage('Ошибка обновления статуса', 'error');
            }
        });
    }
}

async function loadUserOrders(userId, statusFilter = null) {
    try {
        const orders = await API.OrdersService.getUserOrders(userId);
        const ordersList = document.getElementById('ordersList');
        
        if (!orders || orders.length === 0) {
            ordersList.innerHTML = '<div class="loading">📦 У вас пока нет заказов. Создайте первый!</div>';
            return;
        }
        
        // Фильтрация заказов
        let filteredOrders = orders;
        if (statusFilter) {
            filteredOrders = orders.filter(order => order.status === statusFilter);
        }
        
        if (filteredOrders.length === 0) {
            ordersList.innerHTML = '<div class="loading">Нет заказов с таким статусом</div>';
            return;
        }
        
        ordersList.innerHTML = filteredOrders.map(order => `
            <div class="order-card">
                <div class="order-header">
                    <span class="order-id">Заказ #${order.id}</span>
                    <span class="order-status status-${order.status}">${getStatusText(order.status)}</span>
                </div>
                <div class="order-details">
                    <p><strong>📦 Товар:</strong> ${escapeHtml(order.product)}</p>
                    <p><strong>🔢 Количество:</strong> ${order.quantity}</p>
                    <p><strong>💰 Сумма:</strong> ${formatPrice(order.amount)} ₽</p>
                    <p><strong>📅 Дата:</strong> ${formatDate(order.created_at)}</p>
                </div>
                <div class="order-actions">
                    <button class="btn-status" onclick="openStatusModal(${order.id}, '${order.status}')">✏️ Изменить статус</button>
                    ${order.status !== 'cancelled' && order.status !== 'completed' ? 
                        `<button class="btn-delete" onclick="cancelOrder(${order.id})">❌ Отменить</button>` : ''}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading orders:', error);
        document.getElementById('ordersList').innerHTML = '<div class="loading">⚠️ Ошибка загрузки заказов. Попробуйте позже.</div>';
    }
}

function getStatusText(status) {
    const statuses = {
        'pending': '⏳ В обработке',
        'processing': '🔄 Выполняется',
        'completed': '✅ Завершён',
        'cancelled': '❌ Отменён'
    };
    return statuses[status] || status;
}

function formatPrice(amount) {
    return new Intl.NumberFormat('ru-RU').format(amount);
}

function formatDate(dateString) {
    if (!dateString) return '—';
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function openStatusModal(orderId, currentStatus) {
    const modal = document.getElementById('statusModal');
    document.getElementById('statusOrderId').value = orderId;
    document.getElementById('orderStatus').value = currentStatus;
    modal.style.display = 'block';
}

async function cancelOrder(orderId) {
    if (confirm('Вы уверены, что хотите отменить этот заказ?')) {
        try {
            await API.OrdersService.cancelOrder(orderId);
            const userId = API.getCurrentUserId();
            if (userId) {
                await loadUserOrders(userId);
            }
            showMessage('Заказ отменён', 'success');
        } catch (error) {
            showMessage('Ошибка отмены заказа', 'error');
        }
    }
}

function showMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = text;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 2000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
}
