// Конфигурация API
const API_CONFIG = {
    auth: '/api/auth',
    users: '/api/users',
    orders: '/api/orders'
};

// Глобальные настройки для fetch с cookies
const fetchWithCredentials = (url, options = {}) => {
    return fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
};

// Базовый API клиент
class APIClient {
    constructor(baseURL, serviceName) {
        this.baseURL = baseURL;
        this.serviceName = serviceName;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        try {
            const response = await fetchWithCredentials(url, options);
            
            if (response.status === 401) {
                if (window.location.pathname !== '/index.html') {
                    this.logout();
                }
                throw new Error('Сессия истекла');
            }
            
            if (response.status === 403) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || 'Доступ запрещен');
            }
            
            if (response.status === 404) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || 'Ресурс не найден');
            }
            
            if (response.status === 400) {
                const data = await response.json();
                throw new Error(data.error || 'Неверные данные');
            }
            
            if (response.status === 409) {
                const data = await response.json();
                throw new Error(data.error || 'Конфликт данных');
            }
            
            if (response.status === 429) {
                throw new Error('Слишком много запросов, попробуйте позже');
            }
            
            if (response.status === 500) {
                throw new Error('Внутренняя ошибка сервера');
            }
            
            if (response.status === 503) {
                throw new Error('Сервис временно недоступен');
            }
            
            if (response.status === 204) {
                return { success: true };
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`API Error (${this.serviceName}):`, error);
            throw error;
        }
    }

    logout() {
        fetchWithCredentials(`${API_CONFIG.auth}/logout`, {
            method: 'POST'
        }).catch(() => {});
        
        localStorage.removeItem('user_id');
        window.location.href = '/index.html';
    }
}

// Инициализация клиентов
const usersAPI = new APIClient(API_CONFIG.users, 'users');
const ordersAPI = new APIClient(API_CONFIG.orders, 'orders');

// ============ AUTH SERVICE ============
const AuthService = {
    async register(username, email, password) {
        const response = await fetch(`${API_CONFIG.auth}/register`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.status === 201) return data;
        if (response.status === 400) throw new Error(data.error || 'Неверные данные');
        if (response.status === 409) throw new Error(data.error || 'Пользователь уже существует');
        if (response.status === 500) throw new Error('Внутренняя ошибка сервера');
        
        throw new Error(data.error || 'Ошибка регистрации');
    },

    async login(username, password) {
        const response = await fetch(`${API_CONFIG.auth}/login`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.status === 200) {
            if (data.user_id) {
                localStorage.setItem('user_id', data.user_id.toString());
            }
            return { ok: true, ...data };
        }
        
        if (response.status === 400) throw new Error(data.error || 'Неверные данные');
        if (response.status === 401) throw new Error('Неверное имя пользователя или пароль');
        if (response.status === 429) throw new Error('Слишком много попыток входа');
        if (response.status === 500) throw new Error('Внутренняя ошибка сервера');
        
        throw new Error(data.error || 'Ошибка входа');
    },

    async logout() {
        await fetch(`${API_CONFIG.auth}/logout`, {
            method: 'POST',
            credentials: 'include'
        }).catch(() => {});
        
        localStorage.removeItem('user_id');
        window.location.href = '/index.html';
    },

    async verify() {
        const response = await fetch(`${API_CONFIG.auth}/verify`, {
            method: 'POST',
            credentials: 'include'
        });
        return response.status === 200;
    },

    async health() {
        try {
            const response = await fetch(`${API_CONFIG.auth}/health`, {
                method: 'GET',
                credentials: 'include'
            });
            return response.status === 200;
        } catch {
            return false;
        }
    }
};

// ============ USERS SERVICE ============
const UsersService = {
    // GET /users/{id} - получить профиль пользователя
    async getProfile(userId) {
        return await usersAPI.request(`/${userId}`, { method: 'GET' });
    },

    // PUT /users/{id} - обновить профиль
    async updateProfile(userId, userData) {
        return await usersAPI.request(`/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    },

    // DELETE /users/{id} - удалить аккаунт
    async deleteAccount(userId) {
        return await usersAPI.request(`/${userId}`, { method: 'DELETE' });
    },

    // GET /users - получить всех пользователей
    async getAllUsers() {
        return await usersAPI.request('', { method: 'GET' });
    },

    async health() {
        try {
            const response = await fetch(`${API_CONFIG.users}/health`, {
                method: 'GET',
                credentials: 'include'
            });
            return response.status === 200;
        } catch {
            return false;
        }
    }
};

// ============ ORDERS SERVICE ============
const OrdersService = {
    // POST /orders - создать заказ
    async createOrder(total_amount) {
        return await ordersAPI.request('', {
            method: 'POST',
            body: JSON.stringify({ total_amount: parseInt(total_amount) })
        });
    },

    // GET /orders/{id} - получить заказ по ID
    async getOrder(orderId) {
        const order = await ordersAPI.request(`/${orderId}`, { method: 'GET' });
        return order;
    },

    // GET /orders/user/{id} - получить все заказы пользователя
    async getUserOrders(userId) {
        return await ordersAPI.request(`/user/${userId}`, { method: 'GET' });
    },

    // PUT /orders/{id} - обновить статус заказа
    async updateOrderStatus(orderId, status) {
        return await ordersAPI.request(`/${orderId}`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    },

    // DELETE /orders/{id} - отменить/удалить заказ
    async cancelOrder(orderId) {
        return await ordersAPI.request(`/${orderId}`, { method: 'DELETE' });
    },

    async health() {
        try {
            const response = await fetch(`${API_CONFIG.orders}/health`, {
                method: 'GET',
                credentials: 'include'
            });
            return response.status === 200;
        } catch {
            return false;
        }
    }
};

// ============ HELPERS ============
function getCurrentUserId() {
    const id = localStorage.getItem('user_id');
    return id ? parseInt(id) : null;
}

async function getCurrentUser() {
    const userId = getCurrentUserId();
    if (!userId) return null;
    
    try {
        const userData = await UsersService.getProfile(userId);
        return {
            id: userId,
            username: userData.username,
            email: userData.email,
            created_at: userData.created_at
        };
    } catch (error) {
        console.error('Failed to get user info:', error);
        return null;
    }
}

async function checkAllServicesHealth() {
    const results = {
        auth: await AuthService.health(),
        users: await UsersService.health(),
        orders: await OrdersService.health()
    };
    return results;
}

// Экспорт
window.API = {
    AuthService,
    UsersService,
    OrdersService,
    getCurrentUserId,
    getCurrentUser,
    checkAllServicesHealth
};
