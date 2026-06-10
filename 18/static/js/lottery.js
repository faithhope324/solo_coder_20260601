class LotteryWheel {
    constructor() {
        this.canvas = document.getElementById('wheelCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.startBtn = document.getElementById('startBtn');
        this.remainingChancesEl = document.getElementById('remainingChances');
        this.totalPointsEl = document.getElementById('totalPoints');
        this.resultModal = document.getElementById('resultModal');
        this.modalOverlay = document.getElementById('modalOverlay');
        this.closeModalBtn = document.getElementById('closeModalBtn');
        this.recordsListEl = document.getElementById('recordsList');
        this.recordsPaginationEl = document.getElementById('recordsPagination');
        
        this.prizes = [];
        this.isSpinning = false;
        this.currentAngle = 0;
        this.targetAngle = 0;
        this.currentPage = 1;
        this.pageSize = 10;
        this.totalRecords = 0;
        this.ws = null;
        
        this.colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
            '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'
        ];
        
        this.prizeIcons = ['📱', '🎧', '🎫', '💎', '💎', '💎', '💎', '😊'];
        
        this.init();
    }
    
    async init() {
        await this.loadPrizes();
        this.drawWheel();
        this.bindEvents();
        this.loadRecords();
        this.connectWebSocket();
        
        setInterval(() => {
            if (!this.isSpinning) {
                this.updateRemainingChances();
            }
        }, 30000);
    }
    
    async loadPrizes() {
        try {
            const data = await Common.request('/api/prizes/', { method: 'GET' });
            if (data.success) {
                this.prizes = data.prizes;
                this.updatePrizeList();
                this.drawWheel();
            }
        } catch (error) {
            console.error('Failed to load prizes:', error);
        }
    }
    
    updatePrizeList() {
        this.prizes.forEach(prize => {
            const stockEl = document.getElementById(`stock-${prize.id}`);
            if (stockEl) {
                stockEl.textContent = prize.stock;
            }
        });
    }
    
    drawWheel() {
        const canvas = this.canvas;
        const ctx = this.ctx;
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(centerX, centerY) - 10;
        const sliceAngle = (2 * Math.PI) / this.prizes.length;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        for (let i = 0; i < this.prizes.length; i++) {
            const startAngle = this.currentAngle + i * sliceAngle - Math.PI / 2;
            const endAngle = startAngle + sliceAngle;
            
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            ctx.closePath();
            
            ctx.fillStyle = this.colors[i % this.colors.length];
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 3;
            ctx.stroke();
            
            ctx.save();
            ctx.translate(centerX, centerY);
            ctx.rotate(startAngle + sliceAngle / 2);
            
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 20px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            const icon = this.prizeIcons[i] || '🎁';
            ctx.font = '32px Arial';
            ctx.fillText(icon, radius * 0.6, -20);
            
            ctx.font = 'bold 14px Arial';
            const prizeName = this.prizes[i]?.name || '';
            const displayName = prizeName.length > 6 ? prizeName.substring(0, 6) + '...' : prizeName;
            ctx.fillText(displayName, radius * 0.6, 10);
            
            ctx.restore();
        }
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, 70, 0, 2 * Math.PI);
        ctx.fillStyle = '#fff';
        ctx.fill();
        ctx.strokeStyle = '#667eea';
        ctx.lineWidth = 4;
        ctx.stroke();
        
        const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 70);
        gradient.addColorStop(0, '#667eea');
        gradient.addColorStop(1, '#764ba2');
        ctx.beginPath();
        ctx.arc(centerX, centerY, 60, 0, 2 * Math.PI);
        ctx.fillStyle = gradient;
        ctx.fill();
        
        ctx.fillStyle = '#fff';
        ctx.font = 'bold 18px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('点击', centerX, centerY - 8);
        ctx.fillText('抽奖', centerX, centerY + 15);
    }
    
    animate() {
        if (!this.isSpinning) return;
        
        const diff = this.targetAngle - this.currentAngle;
        if (Math.abs(diff) < 0.01) {
            this.currentAngle = this.targetAngle;
            this.isSpinning = false;
            this.drawWheel();
            this.showResult();
            return;
        }
        
        const easeOut = 0.05;
        this.currentAngle += diff * easeOut;
        
        this.drawWheel();
        requestAnimationFrame(() => this.animate());
    }
    
    async startDraw() {
        if (this.isSpinning) return;
        
        const remaining = parseInt(this.remainingChancesEl.textContent);
        if (remaining <= 0) {
            Common.showToast('今日抽奖次数已用完，请明天再来', 'warning');
            return;
        }
        
        this.isSpinning = true;
        this.startBtn.classList.add('spinning');
        this.startBtn.disabled = true;
        
        try {
            const data = await Common.request('/api/draw/', { method: 'POST' });
            
            if (data.success) {
                this.currentResult = data.prize;
                this.remainingChancesEl.textContent = data.remaining_chances;
                
                if (data.prize.points_value) {
                    const currentPoints = parseInt(this.totalPointsEl.textContent) || 0;
                    this.totalPointsEl.textContent = currentPoints + data.prize.points_value;
                }
                
                const prizeIndex = data.prize_index;
                const sliceAngle = (2 * Math.PI) / this.prizes.length;
                const spins = 5 + Math.floor(Math.random() * 3);
                this.targetAngle = this.currentAngle + 
                    spins * 2 * Math.PI + 
                    (2 * Math.PI - prizeIndex * sliceAngle - sliceAngle / 2);
                
                this.animate();
            } else {
                this.isSpinning = false;
                this.startBtn.classList.remove('spinning');
                this.startBtn.disabled = parseInt(this.remainingChancesEl.textContent) <= 0;
                Common.showToast(data.message || '抽奖失败，请重试', 'error');
            }
        } catch (error) {
            console.error('Draw failed:', error);
            this.isSpinning = false;
            this.startBtn.classList.remove('spinning');
            this.startBtn.disabled = parseInt(this.remainingChancesEl.textContent) <= 0;
            
            if (error.status === 429) {
                Common.showToast('操作过于频繁，请稍后再试', 'warning');
            } else {
                Common.showToast('网络错误，请重试', 'error');
            }
        }
    }
    
    showResult() {
        if (!this.currentResult) return;
        
        const prize = this.currentResult;
        const resultIcon = document.getElementById('resultIcon');
        const resultPrizeType = document.getElementById('resultPrizeType');
        const resultPrizeName = document.getElementById('resultPrizeName');
        const resultMessage = document.getElementById('resultMessage');
        
        resultIcon.textContent = this.getPrizeIcon(prize.prize_type);
        resultPrizeType.textContent = prize.prize_type_display;
        resultPrizeName.textContent = prize.name;
        
        if (prize.is_win && prize.prize_type < 8) {
            resultMessage.textContent = `恭喜您获得 ${prize.points_value} 积分！`;
            resultPrizeType.style.color = '#e74c3c';
        } else {
            resultMessage.textContent = '感谢参与，下次继续努力！';
            resultPrizeType.style.color = '#95a5a6';
        }
        
        this.resultModal.style.display = 'flex';
        this.startBtn.classList.remove('spinning');
        this.startBtn.disabled = parseInt(this.remainingChancesEl.textContent) <= 0;
        
        this.loadPrizes();
        this.loadRecords();
    }
    
    getPrizeIcon(prizeType) {
        const icons = {
            1: '📱',
            2: '🎧',
            3: '🎫',
            4: '💎',
            5: '💎',
            6: '💎',
            7: '💎',
            8: '😊'
        };
        return icons[prizeType] || '🎁';
    }
    
    closeResultModal() {
        this.resultModal.style.display = 'none';
        this.currentResult = null;
    }
    
    async updateRemainingChances() {
        try {
            const data = await Common.request('/api/chances/', { method: 'GET' });
            if (data.success) {
                this.remainingChancesEl.textContent = data.remaining_chances;
                this.startBtn.disabled = data.remaining_chances <= 0;
            }
        } catch (error) {
            console.error('Failed to update chances:', error);
        }
    }
    
    async loadRecords() {
        try {
            const data = await Common.request(
                `/api/records/?page=${this.currentPage}&page_size=${this.pageSize}`,
                { method: 'GET' }
            );
            
            if (data.success) {
                this.totalRecords = data.total;
                this.renderRecords(data.records);
                this.renderPagination();
            }
        } catch (error) {
            console.error('Failed to load records:', error);
            this.recordsListEl.innerHTML = '<div class="no-records">加载失败，请重试</div>';
        }
    }
    
    renderRecords(records) {
        if (!records || records.length === 0) {
            this.recordsListEl.innerHTML = '<div class="no-records">暂无抽奖记录</div>';
            return;
        }
        
        const html = records.map(record => `
            <div class="record-item fade-in">
                <div class="record-info">
                    <div class="record-prize ${record.is_win ? 'record-win' : 'record-lose'}">
                        ${record.is_win ? '🎉' : '😊'} ${record.prize_name}
                    </div>
                    <div class="record-time">${record.created_at}</div>
                </div>
                <span class="record-badge" style="background: ${record.is_win ? '#e74c3c' : '#95a5a6'}">
                    ${this.getPrizeTypeName(record.prize_type)}
                </span>
            </div>
        `).join('');
        
        this.recordsListEl.innerHTML = html;
    }
    
    getPrizeTypeName(prizeType) {
        const types = {
            1: '一等奖',
            2: '二等奖',
            3: '三等奖',
            4: '四等奖',
            5: '五等奖',
            6: '六等奖',
            7: '七等奖',
            8: '八等奖'
        };
        return types[prizeType] || '参与奖';
    }
    
    renderPagination() {
        const totalPages = Math.ceil(this.totalRecords / this.pageSize);
        
        if (totalPages <= 1) {
            this.recordsPaginationEl.innerHTML = '';
            return;
        }
        
        let html = '';
        
        html += `<button class="page-btn" ${this.currentPage === 1 ? 'disabled' : ''} data-page="prev">上一页</button>`;
        
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, startPage + 4);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="page-btn ${i === this.currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }
        
        html += `<button class="page-btn" ${this.currentPage === totalPages ? 'disabled' : ''} data-page="next">下一页</button>`;
        
        this.recordsPaginationEl.innerHTML = html;
    }
    
    changePage(page) {
        const totalPages = Math.ceil(this.totalRecords / this.pageSize);
        
        if (page === 'prev') {
            this.currentPage = Math.max(1, this.currentPage - 1);
        } else if (page === 'next') {
            this.currentPage = Math.min(totalPages, this.currentPage + 1);
        } else {
            this.currentPage = parseInt(page);
        }
        
        this.loadRecords();
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/lottery/`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.sendWebSocketMessage({ type: 'get_chances' });
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('WebSocket message parse error:', error);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected, reconnecting...');
                setTimeout(() => this.connectWebSocket(), 3000);
            };
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
        }
    }
    
    sendWebSocketMessage(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'chances_update':
                this.remainingChancesEl.textContent = data.remaining_chances;
                this.startBtn.disabled = data.remaining_chances <= 0;
                break;
            case 'lottery_result':
                this.loadRecords();
                break;
            case 'pong':
                break;
        }
    }
    
    bindEvents() {
        this.startBtn.addEventListener('click', () => this.startDraw());
        
        this.closeModalBtn.addEventListener('click', () => this.closeResultModal());
        this.modalOverlay.addEventListener('click', () => this.closeResultModal());
        
        this.recordsPaginationEl.addEventListener('click', (e) => {
            const target = e.target.closest('.page-btn');
            if (target && !target.disabled) {
                const page = target.dataset.page;
                this.changePage(page);
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.resultModal.style.display === 'flex') {
                this.closeResultModal();
            }
            if (e.key === 'Enter' && !this.isSpinning && this.resultModal.style.display !== 'flex') {
                this.startDraw();
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.lotteryWheel = new LotteryWheel();
});
