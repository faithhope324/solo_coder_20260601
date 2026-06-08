const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const resultsSection = document.getElementById('resultsSection');
const loading = document.getElementById('loading');
const previewImage = document.getElementById('previewImage');
const classificationResults = document.getElementById('classificationResults');
const similarImages = document.getElementById('similarImages');

let selectedFile = null;

uploadArea.addEventListener('click', () => {
    fileInput.click();
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('请选择图片文件');
        return;
    }
    
    selectedFile = file;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        uploadArea.innerHTML = `
            <div class="upload-icon">✅</div>
            <p class="upload-text">${file.name}</p>
            <p class="upload-hint">点击重新选择或拖放其他图片</p>
        `;
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

analyzeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    resultsSection.style.display = 'none';
    loading.style.display = 'block';
    analyzeBtn.disabled = true;
    
    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('top_k', 4);
    
    try {
        const response = await fetch('/api/classify_and_search', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
        } else {
            alert('识别失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('网络错误，请重试');
    } finally {
        loading.style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

function displayResults(data) {
    previewImage.src = data.image_url;
    
    classificationResults.innerHTML = '';
    
    data.predictions.forEach((pred, index) => {
        const isTop = index === 0;
        const confPercent = (pred.confidence * 100).toFixed(1);
        
        const item = document.createElement('div');
        item.className = `prediction-item ${isTop ? 'top' : ''}`;
        item.style.borderLeftColor = pred.color;
        
        item.innerHTML = `
            <span class="prediction-class">${pred.class}</span>
            <span class="prediction-conf" style="color: ${pred.color}">${confPercent}%</span>
            <div class="prediction-bar">
                <div class="prediction-bar-fill" style="width: ${confPercent}%; background: ${pred.color}"></div>
            </div>
        `;
        
        classificationResults.appendChild(item);
        
        if (isTop) {
            const desc = document.createElement('div');
            desc.className = 'description';
            desc.textContent = pred.description;
            classificationResults.appendChild(desc);
        }
    });
    
    similarImages.innerHTML = '';
    
    if (data.similar_images && data.similar_images.length > 0) {
        data.similar_images.forEach((sim) => {
            const simPercent = (sim.similarity * 100).toFixed(1);
            
            const item = document.createElement('div');
            item.className = 'similar-item';
            item.innerHTML = `
                <img src="${sim.url}" alt="相似图片">
                <div class="similar-overlay">
                    <div class="similar-label">${sim.label}</div>
                    <div class="similar-sim">相似度: ${simPercent}%</div>
                </div>
            `;
            
            similarImages.appendChild(item);
        });
    } else {
        const noSimilar = document.createElement('div');
        noSimilar.className = 'no-similar';
        noSimilar.innerHTML = `
            <div style="font-size: 3rem; margin-bottom: 10px;">🔍</div>
            <p>暂无相似图片数据</p>
            <p style="font-size: 0.9rem; margin-top: 5px;">请先添加训练图片并构建索引</p>
        `;
        similarImages.appendChild(noSimilar);
    }
    
    resultsSection.style.display = 'grid';
}
