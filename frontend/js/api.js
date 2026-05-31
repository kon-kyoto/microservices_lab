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
            
            // 401 - не авторизован
            if (response.status === 401) {
                this.logout();
                throw new Error('Сессия истекла, войдите снова');
            }
            
            // 403 - доступ запрещен
            if (response.status === 403) {
                throw new Error('Доступ запрещен');
            }
            
            // 404 - не найдено
            if (response.status === 404) {
                throw new Error('Ресурс не найден');
            }
            
            // 409 - конфликт
            if (response.status === 409) {
                const data = await response.json();
                throw new Error(data.error || 'Конфликт данных');
            }
            
            // 429 - слишком много запросов
            if (response.status === 429) {
                throw new Error('Слишком много запросов, попробуйте позже');
            }
            
            // 400 - плохой запрос
            if (response.status === 400) {
                const data = await response.json();
                throw new Error(data.error || 'Неверные данные');
            }
            
            // 500 - внутренняя ошибка сервера
            if (response.status === 500) {
                throw new Error('Внутренняя ошибка сервера');
            }
            
            // 503 - сервис недоступен
            if (response.status === 503) {
                throw new Error('Сервис временно недоступен');
            }
            
            // Для 204 No Content
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
const authAPI = new APIClient(API_CONFIG.auth, 'auth');
const usersAPI = new APIClient(API_CONFIG.users, 'users');
const ordersAPI = new APIClient(API_CONFIG.orders, 'orders');

// Auth Service
const AuthService = {
    async register(username, email, password) {
        const response = await fetch(`${API_CONFIG.auth}/register`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        // 201 - успешная регистрация
        if (response.status === 201) {
            const data = await response.json();
            return data;
        }
        
        // 400 - плохой запрос
        if (response.status === 400) {
            const data = await response.json();
            throw new Error(data.error || 'Неверные данные');
        }
        
        // 409 - конфликт (пользователь существует)
        if (response.status === 409) {
            const data = await response.json();
            throw new Error(data.error || 'Пользователь уже существует');
        }
        
        // 500 - ошибка сервера
        if (response.status === 500) {
            throw new Error('Внутренняя ошибка сервера');
        }
        
        const data = await response.json();
        return data;
    },

    async login(username, password) {
        const response = await fetch(`${API_CONFIG.auth}/login`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        // 200 - успешный вход
        if (response.status === 200) {
            const data = await response.json();
            if (data.user_id) {
                localStorage.setItem('user_id', data.user_id);
            }
            return { ok: true, ...data };
        }
        
        // 400 - плохой запрос
        if (response.status === 400) {
            const data = await response.json();
            throw new Error(data.error || 'Неверные данные');
        }
        
        // 401 - неверные учетные данные
        if (response.status === 401) {
            throw new Error('Неверное имя пользователя или пароль');
        }
        
        // 429 - слишком много попыток
        if (response.status === 429) {
            throw new Error('Слишком много попыток входа, попробуйте позже');
        }
        
        // 500 - ошибка сервера
        if (response.status === 500) {
            throw new Error('Внутренняя ошибка сервера');
        }
        
        const data = await response.json();
        return { ok: false, ...data };
    },

    async logout() {
        await fetch(`${API_CONFIG.auth}/logout`, {
            method: 'POST',
            credentials: 'include'
        }).catch(() => {});
        
        localStorage.removeItem('user_id');
        window.location.href = '/index.html';
    },

    async checkAuth() {
        try {
            const response = await fetch(`${API_CONFIG.auth}/verify`, {
                method: 'POST',
                credentials: 'include'
            });
            
            // 200 - авторизован
            if (response.status === 200) {
                return true;
            }
            
            // 401 - не авторизован
            if (response.status === 401) {
                return false;
            }
            
            // 500 - ошибка сервера
            return false;
        } catch {
            return false;
        }
    },
    
    async getCurrentUser() {
        const userId = localStorage.getItem('user_id');
        if (!userId) return null;
        
        try {
            const user = await UsersService.getProfile(userId);
            return user;
        } catch (error) {
            console.error('Failed to get user info:', error);
            return null;
        }
    }
};

// Users Service
const UsersService = {
    async getProfile(userId) {
        return await usersAPI.request(`/${userId}`, { method: 'GET' });
    },

    async updateProfile(userId, userData) {
        return await usersAPI.request(`/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    },

    async deleteAccount(userId) {
        return await usersAPI.request(`/${userId}`, { method: 'DELETE' });
    },

    async getAllUsers() {
        return await usersAPI.request('', { method: 'GET' });
    }
};

// Orders Service
const OrdersService = {
    async createOrder(orderData) {
        return await ordersAPI.request('', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    },

    async getOrder(orderId) {
        return await ordersAPI.request(`/${orderId}`, { method: 'GET' });
    },

    async getUserOrders(userId) {
        return await ordersAPI.request(`/user/${userId}`, { method: 'GET' });
    },

    async updateOrderStatus(orderId, status) {
        return await ordersAPI.request(`/${orderId}`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    },

    async cancelOrder(orderId) {
        return await ordersAPI.request(`/${orderId}`, { method: 'DELETE' });
    }
};

// Helper functions
function getCurrentUserId() {
    return localStorage.getItem('user_id');
}

async function getCurrentUser() {
    return await AuthService.getCurrentUser();
}

// Health check
async function checkHealth(service) {
    const urls = {
        auth: `${API_CONFIG.auth}/health`,
        users: `${API_CONFIG.users}/health`,
        orders: `${API_CONFIG.orders}/health`
    };
    
    try {
        const response = await fetch(urls[service], {
            method: 'GET',
            credentials: 'include'
        });
        
        // 200 - здоров
        if (response.status === 200) {
            return true;
        }
        
        // 503 - сервис недоступен
        return false;
    } catch {
        return false;
    }
}

// Экспорт
window.API = {
    AuthService,
    UsersService,
    OrdersService,
    getCurrentUserId,
    getCurrentUser,
    checkHealth
};
