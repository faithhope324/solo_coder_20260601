const API = '';
let mode = 'login';

const tabBtns = document.querySelectorAll('.tab-btn');
const form = document.getElementById('authForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoading = submitBtn.querySelector('.btn-loading');
const toastEl = document.getElementById('toast');

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        tabBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        mode = btn.dataset.tab;
        btnText.textContent = mode === 'login' ? '登 录' : '注 册';
    });
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    if (!username || !password) {
        showToast('请填写完整信息', 'error');
        return;
    }

    setLoading(true);
    try {
        const url = mode === 'login' ? '/api/auth/login' : '/api/auth/register';
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        const data = await res.json();
        if (data.code === 0) {
            if (mode === 'register') {
                showToast('注册成功，请登录', 'success');
                tabBtns[0].click();
            } else {
                localStorage.setItem('token', data.data.access_token);
                localStorage.setItem('username', username);
                showToast('登录成功', 'success');
                setTimeout(() => { window.location.href = '/'; }, 600);
            }
        } else {
            showToast(data.message || '操作失败', 'error');
        }
    } catch (err) {
        showToast('网络错误', 'error');
    } finally {
        setLoading(false);
    }
});

function setLoading(loading) {
    submitBtn.disabled = loading;
    btnText.classList.toggle('hidden', loading);
    btnLoading.classList.toggle('hidden', !loading);
}

function showToast(msg, type) {
    toastEl.textContent = msg;
    toastEl.className = `toast ${type}`;
    requestAnimationFrame(() => toastEl.classList.add('show'));
    setTimeout(() => toastEl.classList.remove('show'), 2500);
}

const token = localStorage.getItem('token');
if (token) {
    window.location.href = '/';
}
