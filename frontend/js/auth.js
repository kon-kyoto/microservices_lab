if (document.getElementById('loginForm')) {
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
    
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        const messageDiv = document.getElementById('message');
        
        if (password.length < 6) {
            messageDiv.className = 'message error';
            messageDiv.textContent = 'Пароль должен содержать минимум 6 символов';
            return;
        }
        
        try {
            const result = await API.AuthService.register(username, email, password);
            if (result.user_id) {
                messageDiv.className = 'message success';
                messageDiv.textContent = 'Регистрация успешна! Теперь войдите.';
                document.getElementById('registerForm').reset();
                setTimeout(() => {
                    document.querySelector('[data-tab="login"]').click();
                }, 1500);
            }
        } catch (error) {
            messageDiv.className = 'message error';
            messageDiv.textContent = error.message;
        }
    });
    
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
            }
        } catch (error) {
            messageDiv.className = 'message error';
            messageDiv.textContent = error.message;
        }
    });
}
