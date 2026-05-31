// Конфигурация API
const API_CONFIG = {
    auth: '/api/auth',
    users: '/api/users',
    orders: '/api/orders'
};

// Глобальные настройки для fetch с cookies
const fetchWithCredentials = (url, options = {}) => {
    console.log(`[API Request] ${options.method || 'GET'} ${url}`);
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
            console.log(`[API Response] ${response.status} ${url}`);
            
            // 401 - не авторизован
            if (response.status === 401) {
                if (window.location.pathname !== '/index.html') {
                    this.logout();
                }
                throw new Error('Сессия истекла');
            }
            
            // 403 - доступ запрещен
            if (response.status === 403) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || 'Доступ запрещен');
            }
            
            // 404 - не найдено
            if (response.status === 404) {
                const data = await response.json().catch(() => ({}));
                console.warn(`[404] ${url} - ${data.error || 'Not found'}`);
                return null; // Возвращаем null вместо ошибки
            }
            
            // 400 - плохой запрос
            if (response.status === 400) {
                const data = await response.json();
                throw new Error(data.error || 'Неверные данные');
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
            
            // 500 - внутренняя ошибка сервера
            if (response.status === 500) {
                throw new Error('Внутренняя ошибка сервера');
            }
            
            // 503 - сервис недоступен
            if (response.status === 503) {
                throw new Error('Сервис временно недоступен');
            }
            
            // 204 No Content - нет тела ответа
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
        try {
            const response = await fetch(`${API_CONFIG.auth}/verify`, {
                method: 'POST',
                credentials: 'include'
            });
            return response.status === 200;
        } catch {
            return false;
        }
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
    async getProfile(userId) {
        const result = await usersAPI.request(`/${userId}`, { method: 'GET' });
        if (!result) {
            throw new Error('Пользователь не найден');
        }
        return result;
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
        const result = await usersAPI.request('', { method: 'GET' });
        // Если сервис вернул null (404), возвращаем пустой массив
        return result || [];
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
    async createOrder(total_amount) {
        return await ordersAPI.request('', {
            method: 'POST',
            body: JSON.stringify({ total_amount: parseInt(total_amount) })
        });
    },

    async getOrder(orderId) {
        return await ordersAPI.request(`/${orderId}`, { method: 'GET' });
    },

    async getUserOrders(userId) {
        const orders = await ordersAPI.request(`/user/${userId}`, { method: 'GET' });
        return orders || [];
    },

    async updateOrderStatus(orderId, status) {
        return await ordersAPI.request(`/${orderId}`, {
            method: 'PUT',
            body: JSON.stringify({ status })
        });
    },

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
        // Возвращаем базовую информацию, если профиль не получен
        return {
            id: userId,
            username: `User ${userId}`,
            email: 'unknown@example.com',
            created_at: null
        };
    }
}

async function checkAllServicesHealth() {
    const results = {
        auth: await AuthService.health(),
        users: await UsersService.health(),
        orders: await OrdersService.health()
    };
    console.log('Services health:', results);
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
