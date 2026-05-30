// Конфигурация API (замени на реальные адреса сервисов)
const API_CONFIG = {
    auth: 'http://localhost:5001',    // Сервис auth
    users: 'http://localhost:5002',   // Сервис users
    orders: 'http://localhost:5003'   // Сервис orders
};

// Глобальные настройки для fetch с cookies
const fetchWithCredentials = (url, options = {}) => {
    return fetch(url, {
        ...options,
        credentials: 'include', // ВАЖНО: отправляем и принимаем cookies
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        }
    });
};

// Хранение данных пользователя (токен хранится ТОЛЬКО в cookie)
let currentUser = null;

// Базовый API клиент для микросервисов
class APIClient {
    constructor(baseURL, serviceName) {
        this.baseURL = baseURL;
        this.serviceName = serviceName;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        try {
            const response = await fetchWithCredentials(url, options);
            
            // Если 401, пробуем обновить токен или разлогиниться
            if (response.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    // Повторяем запрос с обновлённой сессией
                    const retryResponse = await fetchWithCredentials(url, options);
                    return await retryResponse.json();
                } else {
                    this.logout();
                    throw new Error('Сессия истекла, войдите снова');
                }
            }
            
            // Для пустых ответов (204 No Content)
            if (response.status === 204) {
                return { success: true };
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Error (${this.serviceName}):`, error);
            throw error;
        }
    }

    async refreshToken() {
        try {
            const response = await fetchWithCredentials(`${API_CONFIG.auth}/refresh`, {
                method: 'POST'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.user) {
                    currentUser = data.user;
                    localStorage.setItem('user_data', JSON.stringify(data.user));
                }
                return true;
            }
            return false;
        } catch {
            return false;
        }
    }

    logout() {
        // Вызываем логаут на сервере для очистки cookie
        fetchWithCredentials(`${API_CONFIG.auth}/logout`, {
            method: 'POST'
        }).catch(() => {});
        
        localStorage.removeItem('user_data');
        currentUser = null;
        window.location.href = '/index.html';
    }

    getCurrentUser() {
        if (currentUser) return currentUser;
        const userData = localStorage.getItem('user_data');
        if (userData) {
            currentUser = JSON.parse(userData);
            return currentUser;
        }
        return null;
    }
}

// Инициализация клиентов для сервисов
const authAPI = new APIClient(API_CONFIG.auth, 'auth');
const usersAPI = new APIClient(API_CONFIG.users, 'users');
const ordersAPI = new APIClient(API_CONFIG.orders, 'orders');

// Методы для работы с Auth сервисом (без явной передачи токена)
const AuthService = {
    async register(username, email, password) {
        const response = await fetchWithCredentials(`${API_CONFIG.auth}/register`, {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
        return await response.json();
    },

    async login(email, password) {
        const response = await fetchWithCredentials(`${API_CONFIG.auth}/login`, {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.user) {
            currentUser = data.user;
            localStorage.setItem('user_data', JSON.stringify(data.user));
        }
        return data;
    },

    async logout() {
        await fetchWithCredentials(`${API_CONFIG.auth}/logout`, {
            method: 'POST'
        }).catch(() => {});
        
        localStorage.removeItem('user_data');
        currentUser = null;
        window.location.href = '/index.html';
    },

    async checkAuth() {
        try {
            const response = await fetchWithCredentials(`${API_CONFIG.auth}/check`, {
                method: 'GET'
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.authenticated && data.user) {
                    currentUser = data.user;
                    localStorage.setItem('user_data', JSON.stringify(data.user));
                    return true;
                }
            }
            return false;
        } catch {
            return false;
        }
    },
    
    async refreshToken() {
        return await authAPI.refreshToken();
    }
};

// Методы для работы с Users сервисом (cookie передаются автоматически)
const UsersService = {
    async getProfile(userId) {
        return await usersAPI.request(`/users/${userId}`, { method: 'GET' });
    },

    async updateProfile(userId, userData) {
        return await usersAPI.request(`/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    },

    async deleteAccount(userId) {
        return await usersAPI.request(`/users/${userId}`, { method: 'DELETE' });
    },

    async getAllUsers() {
        return await usersAPI.request('/users', { method: 'GET' });
    }
};

// Методы для работы с Orders сервисом
const OrdersService = {
    async createOrder(orderData) {
        return await ordersAPI.request('/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    },

    async getOrder(orderId) {
        return await ordersAPI.request(`/orders/${orderId}`, { method: 'GET' });
    },

    async getUserOrders(userId) {
        return await ordersAPI.request(`/orders/user/${userId}`, { method: 'GET' });
    },

    async updateOrderStatus(orderId, status) {
        return await ordersAPI.request(`/orders/${orderId}/status`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    },

    async cancelOrder(orderId) {
        return await ordersAPI.request(`/orders/${orderId}`, { method: 'DELETE' });
    }
};

// Helper для получения текущего пользователя
function getCurrentUser() {
    return authAPI.getCurrentUser();
}

function isAdmin() {
    const user = getCurrentUser();
    return user && user.role === 'admin';
}

// Экспорт для использования в других файлах
window.API = {
    AuthService,
    UsersService,
    OrdersService,
    getCurrentUser,
    isAdmin
};
