const API = '';
let token = localStorage.getItem('token');
let username = localStorage.getItem('username');
let pollingTimers = {};
let refreshTimer = null;

if (!token) {
    window.location.href = '/login';
}

document.getElementById('userName').textContent = username || '';
document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    window.location.href = '/login';
});

document.getElementById('ordersToggle').addEventListener('click', () => {
    const panel = document.getElementById('ordersPanel');
    const arrow = document.getElementById('toggleArrow');
    panel.classList.toggle('open');
    arrow.classList.toggle('open');
});

async function api(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    try {
        const res = await fetch(path, { ...options, headers });
        if (res.status === 401) {
            localStorage.removeItem('token');
            window.location.href = '/login';
            return null;
        }
        return await res.json();
    } catch {
        showToast('网络错误', 'error');
        return null;
    }
}

async function loadProducts() {
    const data = await api('/api/products');
    if (!data || data.code !== 0) return;

    const grid = document.getElementById('productsGrid');
    grid.innerHTML = '';

    data.data.forEach((p, i) => {
        const pct = p.total_stock > 0 ? (p.remaining_stock / p.total_stock) * 100 : 0;
        const barClass = pct > 50 ? 'high' : pct > 20 ? 'mid' : pct > 0 ? 'low' : 'out';
        const btnClass = p.remaining_stock <= 0 ? 'sold-out' : 'active';
        const btnText = p.remaining_stock <= 0 ? '已售罄' : '立即抢购';

        const card = document.createElement('div');
        card.className = 'product-card';
        card.style.animationDelay = `${i * 0.1}s`;
        card.innerHTML = `
            <div class="product-badge">限时秒杀</div>
            <div class="product-name">${p.name}</div>
            <div class="product-price-row">
                <span class="price-symbol">¥</span>
                <span class="price-value">${p.price.toFixed(2)}</span>
                <span class="price-original">¥${(p.price * 100).toFixed(2)}</span>
            </div>
            <div class="stock-section">
                <div class="stock-header">
                    <span class="stock-label">剩余库存</span>
                    <span class="stock-numbers">
                        <span class="stock-remaining">${p.remaining_stock}</span>
                        <span class="stock-total"> / ${p.total_stock}</span>
                    </span>
                </div>
                <div class="stock-bar">
                    <div class="stock-bar-fill ${barClass}" style="width:${pct}%"></div>
                </div>
            </div>
            <button class="seckill-btn ${btnClass}" data-product-id="${p.id}" ${p.remaining_stock <= 0 ? 'disabled' : ''}>
                ${btnText}
            </button>
        `;
        grid.appendChild(card);
    });

    grid.querySelectorAll('.seckill-btn.active').forEach(btn => {
        btn.addEventListener('click', () => handleSeckill(btn));
    });

    document.getElementById('ordersSection').style.display = 'block';
}

async function handleSeckill(btn) {
    const productId = parseInt(btn.dataset.productId);
    btn.className = 'seckill-btn loading';
    btn.textContent = '抢购中...';
    btn.disabled = true;

    const data = await api(`/api/seckill/${productId}`, { method: 'POST' });

    if (!data) {
        resetBtn(btn, productId);
        return;
    }

    if (data.code === 429) {
        showToast(data.message, 'warning');
        resetBtn(btn, productId);
        return;
    }

    if (data.message === '已售罄') {
        showToast('手慢了，已售罄！', 'error');
        btn.className = 'seckill-btn sold-out';
        btn.textContent = '已售罄';
        btn.disabled = true;
        refreshAllStock();
        return;
    }

    if (data.code === 0 && data.data.order_id) {
        showToast('排队中，请等待结果...', 'info');
        pollResult(data.data.order_id, btn, productId);
        refreshAllStock();
        return;
    }

    showToast(data.message || '抢购失败', 'error');
    resetBtn(btn, productId);
}

function resetBtn(btn, productId) {
    btn.className = 'seckill-btn active';
    btn.textContent = '立即抢购';
    btn.disabled = false;
}

async function pollResult(orderId, btn, productId) {
    let attempts = 0;
    const maxAttempts = 30;
    const timerId = setInterval(async () => {
        attempts++;
        if (attempts > maxAttempts) {
            clearInterval(timerId);
            delete pollingTimers[orderId];
            showToast('超时，请查看订单', 'warning');
            resetBtn(btn, productId);
            return;
        }

        const data = await api(`/api/seckill/result/${orderId}`);
        if (!data || !data.data) return;

        const status = data.data.status;
        if (status === 'success') {
            clearInterval(timerId);
            delete pollingTimers[orderId];
            showToast(`🎉 抢购成功！${data.data.product_name || ''}`, 'success');
            resetBtn(btn, productId);
            loadOrders();
            refreshAllStock();
        } else if (status === 'failed') {
            clearInterval(timerId);
            delete pollingTimers[orderId];
            showToast('抢购失败，库存已回滚', 'error');
            resetBtn(btn, productId);
            refreshAllStock();
        }
    }, 1000);

    pollingTimers[orderId] = timerId;
}

async function refreshAllStock() {
    const data = await api('/api/products');
    if (!data || data.code !== 0) return;

    data.data.forEach(p => {
        const btn = document.querySelector(`[data-product-id="${p.id}"]`);
        if (!btn) return;
        const card = btn.closest('.product-card');
        const pct = p.total_stock > 0 ? (p.remaining_stock / p.total_stock) * 100 : 0;
        const barClass = pct > 50 ? 'high' : pct > 20 ? 'mid' : pct > 0 ? 'low' : 'out';

        const remaining = card.querySelector('.stock-remaining');
        if (remaining) remaining.textContent = p.remaining_stock;

        const barFill = card.querySelector('.stock-bar-fill');
        if (barFill) {
            barFill.className = `stock-bar-fill ${barClass}`;
            barFill.style.width = `${pct}%`;
        }

        if (p.remaining_stock <= 0 && !btn.classList.contains('loading')) {
            btn.className = 'seckill-btn sold-out';
            btn.textContent = '已售罄';
            btn.disabled = true;
        }
    });
}

async function loadOrders() {
    const data = await api('/api/orders');
    if (!data || data.code !== 0) return;

    const list = document.getElementById('ordersList');
    if (!data.data || data.data.length === 0) {
        list.innerHTML = '<div class="no-orders">还没有抢到商品，快去抢购吧！</div>';
        return;
    }

    list.innerHTML = data.data.map(o => `
        <div class="order-item">
            <span class="order-product">${o.product_name || '商品'}</span>
            <span class="order-time">${o.created_at ? o.created_at.replace('T', ' ').substring(0, 19) : ''}</span>
            <span class="order-status success">已抢到</span>
        </div>
    `).join('');
}

function showToast(msg, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.transition = 'opacity 0.4s';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

loadProducts();
loadOrders();

refreshTimer = setInterval(() => {
    refreshAllStock();
}, 3000);

window.addEventListener('beforeunload', () => {
    Object.values(pollingTimers).forEach(t => clearInterval(t));
    if (refreshTimer) clearInterval(refreshTimer);
});
