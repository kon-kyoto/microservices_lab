document.addEventListener('DOMContentLoaded', async () => {
    const user = API.getCurrentUser();
    
    // Проверка прав администратора
    if (!user || user.role !== 'admin') {
        window.location.href = '/dashboard.html';
        return;
    }
    
    await loadAllUsers();
    
    // Модальное окно редактирования
    const modal = document.getElementById('editUserModal');
    const closeBtn = document.querySelector('#editUserModal .close-edit');
    
    closeBtn.onclick = () => modal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target === modal) modal.style.display = 'none';
    };
    
    // Редактирование пользователя
    document.getElementById('editUserForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const userId = document.getElementById('editUserId').value;
        const userData = {
            username: document.getElementById('editUsername').value,
            email: document.getElementById('editEmail').value
        };
        
        try {
            const result = await API.UsersService.updateProfile(userId, userData);
            if (result.message || result.id) {
                modal.style.display = 'none';
                await loadAllUsers();
                showUserMessage('✅ Пользователь обновлён', 'success');
            }
        } catch (error) {
            showUserMessage('❌ Ошибка обновления', 'error');
        }
    });
});

async function loadAllUsers() {
    try {
        const users = await API.UsersService.getAllUsers();
        const usersList = document.getElementById('usersList');
        const stats = document.getElementById('userStats');
        
        if (!users || users.length === 0) {
            usersList.innerHTML = '<div class="loading">Нет пользователей</div>';
            stats.textContent = 'Всего: 0';
            return;
        }
        
        stats.innerHTML = `👥 Всего: ${users.length}`;
        
        usersList.innerHTML = users.map(user => `
            <div class="user-card">
                <div class="user-info">
                    <div class="avatar">${getAvatarIcon(user.username)}</div>
                    <div class="user-details">
                        <h3>${escapeHtml(user.username)}</h3>
                        <p>📧 ${escapeHtml(user.email)}</p>
                        <small>🆔 ID: ${user.id} | 👑 Роль: ${user.role || 'user'}</small>
                    </div>
                </div>
                <div class="user-actions">
                    <button class="btn-edit" onclick="editUser(${user.id}, '${escapeHtml(user.username)}', '${escapeHtml(user.email)}')">✏️ Редактировать</button>
                    <button class="btn-delete-user" onclick="deleteUser(${user.id})">🗑️ Удалить</button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading users:', error);
        document.getElementById('usersList').innerHTML = '<div class="loading">⚠️ Ошибка загрузки пользователей</div>';
    }
}

function getAvatarIcon(username) {
    if (!username) return '👤';
    // Эмодзи для разных букв (для красоты)
    const firstChar = username.charAt(0).toLowerCase();
    const emojiMap = {
        'a': '🍎', 'b': '⚽', 'c': '🐱', 'd': '🐶', 'e': '🦅',
        'f': '🌸', 'g': '🎸', 'h': '🏠', 'i': '🍦', 'j': '🤡',
        'k': '🔑', 'l': '🦁', 'm': '🐭', 'n': '📝', 'o': '🦉',
        'p': '🐧', 'q': '👑', 'r': '🐰', 's': '⭐', 't': '🐯',
        'u': '☂️', 'v': '🎻', 'w': '🐺', 'x': '❌', 'y': '💛', 'z': '🦓'
    };
    return emojiMap[firstChar] || '👤';
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function editUser(id, username, email) {
    document.getElementById('editUserId').value = id;
    document.getElementById('editUsername').value = username;
    document.getElementById('editEmail').value = email;
    document.getElementById('editUserModal').style.display = 'block';
}

async function deleteUser(userId) {
    if (confirm('⚠️ Вы уверены, что хотите удалить этого пользователя? Это действие необратимо!')) {
        try {
            await API.UsersService.deleteAccount(userId);
            await loadAllUsers();
            showUserMessage('✅ Пользователь удалён', 'success');
        } catch (error) {
            showUserMessage('❌ Ошибка удаления пользователя', 'error');
        }
    }
}

function showUserMessage(text, type) {
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
