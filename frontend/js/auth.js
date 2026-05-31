// Обработка форм на странице входа
if (document.getElementById('loginForm')) {
    // Переключение табов
    const tabBtns = document.querySelectorAll('.tab-btn');
    const forms = document.querySelectorAll('.auth-form');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            forms.forEach(f => f.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(`${tabId}Form`).classList.add('active');
        });
    });
    
    // Регистрация
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        
        const messageDiv = document.getElementById('message');
        
        // Простая валидация
        if (password.length < 6) {
            messageDiv.className = 'message error';
            messageDiv.textContent = 'Пароль должен содержать минимум 6 символов';
            return;
        }
        
        try {
            const result = await API.AuthService.register(username, email, password);
            
            if (result.message || result.id) {
                messageDiv.className = 'message success';
                messageDiv.textContent = 'Регистрация успешна! Теперь войдите.';
                
                // Очищаем форму
                document.getElementById('registerForm').reset();
                // Переключаемся на вкладку входа
                setTimeout(() => {
                    document.querySelector('[data-tab="login"]').click();
                }, 1500);
            } else if (result.error) {
                throw new Error(result.error);
            }
        } catch (error) {
            messageDiv.className = 'message error';
            messageDiv.textContent = error.message || 'Ошибка регистрации';
        }
    });
    
    // Вход
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        
        const messageDiv = document.getElementById('message');
        
        try {
            const result = await API.AuthService.login(username, password);
            
            if (result.ok) {
                messageDiv.className = 'message success';
                messageDiv.textContent = 'Вход выполнен! Перенаправление...';
                
                setTimeout(() => {
                    window.location.href = '/dashboard.html';
                }, 1000);
            } else {
                throw new Error(result.error || 'Ошибка входа');
            }
        } catch (error) {
            messageDiv.className = 'message error';
            messageDiv.textContent = error.message || 'Неверное имя пользователя или пароль';
        }
    });
}

// Проверка авторизации на защищённых страницах
if (window.location.pathname !== '/index.html' && 
    window.location.pathname !== '/') {
    // Проверяем аутентификацию через API
    API.AuthService.checkAuth().then(isAuthenticated => {
        if (!isAuthenticated) {
            window.location.href = '/index.html';
        }
    }).catch(() => {
        window.location.href = '/index.html';
    });
}

// Кнопка выхода (если есть на странице)
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
        await API.AuthService.logout();
    });
}
