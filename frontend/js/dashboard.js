let currentUser = null;

document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    await loadUserData();
    await updateServicesStatus();
    
    initTabs();
    initEventListeners();
    await loadOrders();
    await loadAllUsers();
});

async function checkAuth() {
    const isAuthenticated = await API.AuthService.verify();
    if (!isAuthenticated) {
        window.location.href = '/index.html';
    }
}

async function loadUserData() {
    currentUser = await API.getCurrentUser();
    if (currentUser) {
        document.getElementById('userName').textContent = currentUser.username;
        document.getElementById('userEmail').textContent = currentUser.email;
        document.getElementById('userCreated').textContent = `Зарегистрирован: ${formatDate(currentUser.created_at)}`;
        document.getElementById('profileUsername').value = currentUser.username;
        document.getElementById('profileEmail').value = currentUser.email;
    }
}

async function updateServicesStatus() {
    const status = await API.checkAllServicesHealth();
    const statusHtml = `
        <span class="service-status ${status.auth ? 'status-healthy' : 'status-unhealthy'}" title="Auth"></span>
        <span class="service-status ${status.users ? 'status-healthy' : 'status-unhealthy'}" title="Users"></span>
        <span class="service-status ${status.orders ? 'status-healthy' : 'status-unhealthy'}" title="Orders"></span>
    `;
    document.getElementById('serviceStatus').innerHTML = statusHtml;
}

function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn-dash');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${tabId}Tab`).classList.add('active');
        });
    });
}

function initEventListeners() {
    // Обновление статуса сервисов
    document.getElementById('refreshStatusBtn').addEventListener('click', updateServicesStatus);
    
    // Выход
    document.getElementById('logoutBtn').addEventListener('click', () => API.AuthService.logout());
    
    // Создание заказа
    const modal = document.getElementById('orderModal');
    document.getElementById('createOrderBtn').onclick = () => modal.style.display = 'block';
    document.querySelector('#orderModal .close').onclick = () => modal.style.display = 'none';
    
    document.getElementById('createOrderForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const total_amount = parseFloat(document.getElementById('orderAmount').value);
        
        if (isNaN(total_amount) || total_amount < 1) {
            showMessage('Сумма должна быть больше 0', 'error');
            return;
        }
        
        try {
            const result = await API.OrdersService.createOrder(total_amount);
            if (result.order_id) {
                modal.style.display = 'none';
                document.getElementById('createOrderForm').reset();
                await loadOrders();
                showMessage('Заказ успешно создан!', 'success');
            }
        } catch (error) {
            showMessage(error.message, 'error');
        }
    });
    
    // Обновление статуса заказа
    const statusModal = document.getElementById('statusModal');
    document.querySelector('#statusModal .close-status').onclick = () => statusModal.style.display = 'none';
    
    document.getElementById('statusForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const orderId = document.getElementById('statusOrderId').value;
        const status = document.getElementById('orderStatus').value;
        
        try {
            await API.OrdersService.updateOrderStatus(orderId, status);
            statusModal.style.display = 'none';
            await loadOrders();
            showMessage('Статус заказа обновлён', 'success');
        } catch (error) {
            showMessage(error.message, 'error');
        }
    });
    
    // Обновление профиля
    document.getElementById('updateProfileForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const newUsername = document.getElementById('profileUsername').value;
        const newEmail = document.getElementById('profileEmail').value;
        
        try {
            await API.UsersService.updateProfile(currentUser.id, {
                username: newUsername,
                email: newEmail
            });
            await loadUserData();
            showMessage('Профиль обновлён!', 'success');
        } catch (error) {
            showMessage(error.message, 'error');
        }
    });
    
    // Удаление аккаунта
    document.getElementById('deleteAccountBtn').addEventListener('click', async () => {
        if (confirm('⚠️ ВНИМАНИЕ! Это действие НЕОБРАТИМО. Вы уверены, что хотите удалить аккаунт?')) {
            if (confirm('ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ! Все ваши заказы будут удалены. Продолжить?')) {
                try {
                    await API.UsersService.deleteAccount(currentUser.id);
                    await API.AuthService.logout();
                } catch (error) {
                    showMessage(error.message, 'error');
                }
            }
        }
    });
    
    // API Тесты
    document.getElementById('testGetUsers').addEventListener('click', async () => {
        try {
            const users = await API.UsersService.getAllUsers();
            document.getElementById('resultGetUsers').textContent = JSON.stringify(users, null, 2);
        } catch (error) {
            document.getElementById('resultGetUsers').textContent = `Error: ${error.message}`;
        }
    });
    
    document.getElementById('testGetOrders').addEventListener('click', async () => {
        try {
            const orders = await API.OrdersService.getUserOrders(currentUser.id);
            document.getElementById('resultGetOrders').textContent = JSON.stringify(orders, null, 2);
        } catch (error) {
            document.getElementById('resultGetOrders').textContent = `Error: ${error.message}`;
        }
    });
    
    document.getElementById('testCreateOrder').addEventListener('click', async () => {
        try {
            const result = await API.OrdersService.createOrder(5000);
            document.getElementById('resultCreateOrder').textContent = JSON.stringify(result, null, 2);
            await loadOrders();
        } catch (error) {
            document.getElementById('resultCreateOrder').textContent = `Error: ${error.message}`;
        }
    });
}

async function loadOrders(statusFilter = null) {
    if (!currentUser) return;
    
    try {
        let orders = await API.OrdersService.getUserOrders(currentUser.id);
        const ordersList = document.getElementById('ordersList');
        
        if (!orders || orders.length === 0) {
            ordersList.innerHTML = '<div class="loading">📦 У вас пока нет заказов. Создайте первый!</div>';
            return;
        }
        
        if (statusFilter && statusFilter !== 'all') {
            orders = orders.filter(order => order.status === statusFilter);
        }
        
        if (orders.length === 0) {
            ordersList.innerHTML = '<div class="loading">Нет заказов с таким статусом</div>';
            return;
        }
        
        ordersList.innerHTML = orders.map(order => `
            <div class="order-card">
                <div class="order-header">
                    <span class="order-id">Заказ #${order.id}</span>
                    <span class="order-status status-${order.status}">${getStatusText(order.status)}</span>
                </div>
                <div class="order-details">
                    <p><strong>💰 Сумма:</strong> ${formatPrice(order.total_amount)} ₽</p>
                    <p><strong>📅 Дата создания:</strong> ${formatDate(order.created_at)}</p>
                    <p><strong>🆔 ID заказа:</strong> ${order.id}</p>
                </div>
                <div class="order-actions">
                    <button class="btn-status" onclick="openStatusModal(${order.id}, '${order.status}')">✏️ Изменить статус</button>
                    ${order.status !== 'cancelled' && order.status !== 'delivered' ? 
                        `<button class="btn-delete" onclick="cancelOrder(${order.id})">❌ Отменить</button>` : ''}
                </div>
            </div>
        `).join('');
        
        // Настройка фильтров
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.removeEventListener('click', handleFilterClick);
            btn.addEventListener('click', handleFilterClick);
        });
        
    } catch (error) {
        console.error('Error loading orders:', error);
        document.getElementById('ordersList').innerHTML = '<div class="loading">⚠️ Ошибка загрузки заказов</div>';
    }
}

function handleFilterClick(e) {
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    const status = e.target.dataset.status;
    loadOrders(status === 'all' ? null : status);
}

async function loadAllUsers() {
    try {
        const users = await API.UsersService.getAllUsers();
        const container = document.getElementById('allUsersList');
        
        if (!users || users.length === 0) {
            container.innerHTML = '<div class="loading">Нет пользователей</div>';
            return;
        }
        
        container.innerHTML = users.map(user => `
            <div class="user-item">
                <div>
                    <strong>${escapeHtml(user.username)}</strong><br>
                    <small>📧 ${escapeHtml(user.email)}</small><br>
                    <small>🆔 ID: ${user.id} | 📅 ${formatDate(user.created_at)}</small>
                </div>
                ${user.id === currentUser?.id ? '<span class="status-badge" style="background:#667eea; color:white;">Это вы</span>' : ''}
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading users:', error);
        document.getElementById('allUsersList').innerHTML = '<div class="loading">⚠️ Ошибка загрузки пользователей</div>';
    }
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
            await loadOrders();
            showMessage('Заказ отменён', 'success');
        } catch (error) {
            showMessage(error.message, 'error');
        }
    }
}

function getStatusText(status) {
    const statuses = {
        'pending': '⏳ В обработке',
        'processing': '🔄 Выполняется',
        'shipped': '🚚 Отправлен',
        'delivered': '✅ Доставлен',
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
