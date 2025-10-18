// Thai License Plate Recognition - Web App
// Real-time camera support, WebSocket, and Arduino control

// ===== Global State =====
let currentPage = 1;
let totalPages = 1;
const pageLimit = 20;
let ws = null;
let reconnectInterval = null;
let sessionToken = localStorage.getItem('session_token') || null;
let currentUser = null;

// Camera state
let cameraStream = null;
let isCameraActive = false;
let captureInterval = null;
const CAMERA_CAPTURE_INTERVAL = 2000; // Capture every 2 seconds

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Thai LPR App initializing...');
    
    // Check authentication
    checkAuth();
    
    // Setup event listeners
    setupEventListeners();
    
    // Connect WebSocket
    connectWebSocket();
    
    // Load initial data
    loadRecords();
    loadStats();
});

// ===== Authentication =====
async function checkAuth() {
    if (!sessionToken) {
        showLoginModal();
        return;
    }
    
    try {
        const response = await fetch(`/api/auth/me?session_token=${sessionToken}`);
        const data = await response.json();
        
        if (data.success) {
            currentUser = data.user;
            updateUserUI();
        } else {
            showLoginModal();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLoginModal();
    }
}

function updateUserUI() {
    if (currentUser) {
        document.getElementById('username').textContent = currentUser.username;
        document.getElementById('logoutBtn').style.display = 'inline-block';
        
        // Show admin tab if user is admin
        if (currentUser.role === 'admin') {
            document.querySelectorAll('.admin-only').forEach(el => {
                el.style.display = 'block';
            });
        }
        
        hideLoginModal();
    }
}

function showLoginModal() {
    document.getElementById('loginModal').classList.add('active');
}

function hideLoginModal() {
    document.getElementById('loginModal').classList.remove('active');
    document.getElementById('registerModal').classList.remove('active');
}

// ===== Event Listeners =====
function setupEventListeners() {
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Upload area
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag & drop
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
        const file = e.dataTransfer.files[0];
        if (file) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect();
        }
    });
    
    // Upload button
    document.getElementById('uploadBtn')?.addEventListener('click', processUpload);
    
    // Camera button (will add to HTML)
    document.getElementById('cameraBtn')?.addEventListener('click', toggleCamera);
    
    // Pagination
    document.getElementById('prevPage')?.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadRecords();
        }
    });
    
    document.getElementById('nextPage')?.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            loadRecords();
        }
    });
    
    // Refresh button
    document.getElementById('refreshBtn')?.addEventListener('click', () => {
        currentPage = 1;
        loadRecords();
    });
    
    // Search
    let searchTimeout;
    document.getElementById('searchInput')?.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentPage = 1;
            loadRecords(e.target.value);
        }, 500);
    });
    
    // Admin controls
    document.getElementById('testGateBtn')?.addEventListener('click', testGate);
    document.getElementById('forceCloseBtn')?.addEventListener('click', forceCloseGate);
    document.getElementById('saveSettingsBtn')?.addEventListener('click', saveSettings);
    document.getElementById('exportDataBtn')?.addEventListener('click', exportData);
    document.getElementById('clearOldDataBtn')?.addEventListener('click', clearOldData);
    
    // Auth forms
    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('registerForm')?.addEventListener('submit', handleRegister);
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);
    document.getElementById('showRegister')?.addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('loginModal').classList.remove('active');
        document.getElementById('registerModal').classList.add('active');
    });
    document.getElementById('showLogin')?.addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('registerModal').classList.remove('active');
        document.getElementById('loginModal').classList.add('active');
    });
}

// ===== Tab Switching =====
function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tabName);
    });
    
    // Load data for active tab
    if (tabName === 'records') {
        loadRecords();
    } else if (tabName === 'admin') {
        loadStats();
    }
}

// ===== Camera Functions =====
async function toggleCamera() {
    if (isCameraActive) {
        stopCamera();
    } else {
        await startCamera();
    }
}

async function startCamera() {
    try {
        // Request camera access
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'environment', // Use rear camera on mobile
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        });
        
        // Show video preview
        const videoPreview = document.getElementById('cameraPreview');
        if (videoPreview) {
            videoPreview.srcObject = cameraStream;
            videoPreview.play();
        }
        
        isCameraActive = true;
        
        // Update UI
        const cameraBtn = document.getElementById('cameraBtn');
        if (cameraBtn) {
            cameraBtn.textContent = '⏹️ Stop Camera';
            cameraBtn.classList.add('btn-danger');
            cameraBtn.classList.remove('btn-secondary');
        }
        
        // Show camera section
        document.getElementById('cameraSection').style.display = 'block';
        document.getElementById('uploadArea').style.display = 'none';
        
        // Start auto-capture
        startAutoCapture();
        
        showNotification('Camera started! Detecting plates...', 'success');
        
    } catch (error) {
        console.error('Camera error:', error);
        showNotification('Failed to access camera: ' + error.message, 'error');
    }
}

function stopCamera() {
    // Stop camera stream
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    // Stop auto-capture
    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
    
    isCameraActive = false;
    
    // Update UI
    const cameraBtn = document.getElementById('cameraBtn');
    if (cameraBtn) {
        cameraBtn.textContent = '📷 Open Camera';
        cameraBtn.classList.remove('btn-danger');
        cameraBtn.classList.add('btn-secondary');
    }
    
    // Hide camera section
    document.getElementById('cameraSection').style.display = 'none';
    document.getElementById('uploadArea').style.display = 'block';
    
    showNotification('Camera stopped', 'info');
}

function startAutoCapture() {
    captureInterval = setInterval(async () => {
        if (isCameraActive && cameraStream) {
            await captureAndProcess();
        }
    }, CAMERA_CAPTURE_INTERVAL);
}

async function captureAndProcess() {
    try {
        const video = document.getElementById('cameraPreview');
        if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) {
            return;
        }
        
        // Create canvas to capture frame
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        
        // Convert to blob
        canvas.toBlob(async (blob) => {
            if (blob) {
                // Send to API
                const formData = new FormData();
                formData.append('file', blob, 'camera_capture.jpg');
                
                try {
                    const response = await fetch('/detect', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.plate_text) {
                        // Show detection in UI
                        showCameraDetection(result);
                        
                        // Highlight on video (optional)
                        highlightDetection(video, ctx);
                    }
                    
                } catch (error) {
                    console.error('Detection error:', error);
                }
            }
        }, 'image/jpeg', 0.8);
        
    } catch (error) {
        console.error('Capture error:', error);
    }
}

function showCameraDetection(result) {
    const detectionDiv = document.getElementById('cameraDetections');
    if (!detectionDiv) return;
    
    const detectionCard = document.createElement('div');
    detectionCard.className = 'camera-detection-card';
    detectionCard.innerHTML = `
        <div class="detection-time">${new Date().toLocaleTimeString()}</div>
        <div class="detection-plate">${result.plate_text || 'N/A'}</div>
        <div class="detection-province">${result.province_text || ''}</div>
        <div class="detection-confidence">${(result.confidence * 100).toFixed(1)}%</div>
    `;
    
    // Add to top
    detectionDiv.insertBefore(detectionCard, detectionDiv.firstChild);
    
    // Keep only last 10 detections
    while (detectionDiv.children.length > 10) {
        detectionDiv.removeChild(detectionDiv.lastChild);
    }
    
    // Flash effect
    detectionCard.style.animation = 'flash 0.5s ease-out';
}

function highlightDetection(video, ctx) {
    // Flash border
    video.style.border = '4px solid #10b981';
    setTimeout(() => {
        video.style.border = '2px solid #e2e8f0';
    }, 500);
}

// ===== File Upload =====
function handleFileSelect() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) return;
    
    // Show preview
    const preview = document.getElementById('preview');
    const imagePreview = document.getElementById('imagePreview');
    const videoPreview = document.getElementById('videoPreview');
    
    preview.style.display = 'block';
    
    if (file.type.startsWith('image/')) {
        imagePreview.src = URL.createObjectURL(file);
        imagePreview.style.display = 'block';
        videoPreview.style.display = 'none';
    } else if (file.type.startsWith('video/')) {
        videoPreview.src = URL.createObjectURL(file);
        videoPreview.style.display = 'block';
        imagePreview.style.display = 'none';
    }
    
    // Show upload button
    document.getElementById('uploadBtn').style.display = 'inline-block';
    
    // Hide result
    document.getElementById('result').style.display = 'none';
}

async function processUpload() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showNotification('Please select a file', 'error');
        return;
    }
    
    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').style.display = 'none';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        // Choose endpoint based on file type
        const endpoint = file.type.startsWith('video/') ? '/detect-video' : '/detect';
        
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        // Hide loading
        document.getElementById('loading').style.display = 'none';
        
        // Show result
        if (file.type.startsWith('image/')) {
            showImageResult(result);
        } else {
            showVideoResult(result);
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        document.getElementById('loading').style.display = 'none';
        showNotification('Processing failed: ' + error.message, 'error');
    }
}

function showImageResult(result) {
    const resultDiv = document.getElementById('result');
    resultDiv.style.display = 'block';
    
    document.getElementById('plateText').textContent = result.plate_text || 'N/A';
    document.getElementById('provinceText').textContent = result.province_text || 'N/A';
    document.getElementById('confidence').textContent = result.confidence 
        ? (result.confidence * 100).toFixed(2) 
        : 'N/A';
    document.getElementById('gateStatus').textContent = result.gate_opened ? '✅ Opened' : '❌ Not Opened';
    
    showNotification('Detection completed!', 'success');
}

function showVideoResult(result) {
    const resultDiv = document.getElementById('result');
    resultDiv.style.display = 'block';
    
    resultDiv.innerHTML = `
        <h3>Video Processing Complete</h3>
        <div class="result-card">
            <p><strong>Frames Processed:</strong> ${result.frames_processed}</p>
            <p><strong>Unique Plates:</strong> ${result.unique_plates.length}</p>
            <p><strong>Records Saved:</strong> ${result.records_saved}</p>
            <p><strong>Detected Plates:</strong></p>
            <ul style="margin-left: 20px;">
                ${result.unique_plates.map(plate => `<li>${plate}</li>`).join('')}
            </ul>
        </div>
    `;
    
    showNotification('Video processing completed!', 'success');
}

// ===== Records =====
async function loadRecords(searchQuery = '') {
    try {
        let url = `/api/records?page=${currentPage}&limit=${pageLimit}`;
        if (searchQuery) {
            url += `&search=${encodeURIComponent(searchQuery)}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        displayRecords(data.records);
        
        // Update pagination
        const total = data.total || 0;
        totalPages = Math.ceil(total / pageLimit);
        document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${totalPages}`;
        
        // Update button states
        document.getElementById('prevPage').disabled = currentPage === 1;
        document.getElementById('nextPage').disabled = currentPage === totalPages;
        
    } catch (error) {
        console.error('Failed to load records:', error);
        showNotification('Failed to load records', 'error');
    }
}

function displayRecords(records) {
    const tbody = document.getElementById('recordsBody');
    
    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">No records found</td></tr>';
        return;
    }
    
    tbody.innerHTML = records.map(record => `
        <tr>
            <td>${record.id}</td>
            <td class="plate-image-cell">
                ${record.plate_image 
                    ? `<img src="${record.plate_image}" class="plate-thumbnail" alt="Plate" onclick="showImageModal('${record.plate_image}')">`
                    : 'N/A'}
            </td>
            <td><strong>${record.plate_text || 'N/A'}</strong></td>
            <td>${record.province_text || 'N/A'}</td>
            <td>${record.confidence ? (record.confidence * 100).toFixed(1) + '%' : 'N/A'}</td>
            <td>${record.created_at ? new Date(record.created_at).toLocaleString('th-TH') : 'N/A'}</td>
        </tr>
    `).join('');
}

// ===== Admin Functions =====
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        document.getElementById('totalRecords').textContent = data.total_records || 0;
        document.getElementById('todayRecords').textContent = data.today_records || 0;
        document.getElementById('avgConfidence').textContent = ((data.avg_confidence || 0) * 100).toFixed(1) + '%';
        
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function testGate() {
    try {
        const response = await fetch('/api/gate/test', { method: 'POST' });
        const result = await response.json();
        
        showNotification(result.message || 'Gate test command sent', 'success');
        
    } catch (error) {
        console.error('Gate test failed:', error);
        showNotification('Failed to send gate command', 'error');
    }
}

async function forceCloseGate() {
    try {
        const response = await fetch('/api/gate/close', { method: 'POST' });
        const result = await response.json();
        
        showNotification(result.message || 'Gate close command sent', 'success');
        
    } catch (error) {
        console.error('Gate close failed:', error);
        showNotification('Failed to close gate', 'error');
    }
}

async function saveSettings() {
    const settings = {
        gateMode: document.getElementById('gateMode')?.value,
        cooldown: document.getElementById('cooldown')?.value
    };
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        showNotification(result.message || 'Settings saved', 'success');
        
    } catch (error) {
        console.error('Save settings failed:', error);
        showNotification('Failed to save settings', 'error');
    }
}

async function exportData() {
    try {
        window.location.href = '/api/export/csv';
        showNotification('Exporting data...', 'info');
    } catch (error) {
        console.error('Export failed:', error);
        showNotification('Failed to export data', 'error');
    }
}

async function clearOldData() {
    if (!confirm('Clear records older than 30 days?')) return;
    
    try {
        const response = await fetch('/api/records/clear-old?days=30', { method: 'DELETE' });
        const result = await response.json();
        
        showNotification(`Deleted ${result.deleted_count} old records`, 'success');
        loadRecords();
        loadStats();
        
    } catch (error) {
        console.error('Clear data failed:', error);
        showNotification('Failed to clear data', 'error');
    }
}

// ===== WebSocket =====
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('✅ WebSocket connected');
        document.getElementById('wsStatus').textContent = 'Connected';
        document.getElementById('wsStatus').className = 'status-badge connected';
        clearInterval(reconnectInterval);
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('❌ WebSocket disconnected');
        document.getElementById('wsStatus').textContent = 'Disconnected';
        document.getElementById('wsStatus').className = 'status-badge disconnected';
        
        // Auto-reconnect
        reconnectInterval = setInterval(connectWebSocket, 3000);
    };
}

function handleWebSocketMessage(data) {
    if (data.type === 'detection') {
        // Show real-time detection
        addRealtimeLog(`🚗 ${data.plate_text || 'Unknown'} | ${data.province_text || ''} | ${(data.confidence * 100).toFixed(1)}%`);
        
        // Refresh records if on records tab
        const recordsTab = document.getElementById('records');
        if (recordsTab && recordsTab.classList.contains('active')) {
            loadRecords();
        }
    }
    
    if (data.type === 'gate') {
        addRealtimeLog(`🚪 Gate ${data.action}: ${data.plate_text || ''}`);
        updateGateStatus(data.action === 'opened');
    }
}

function addRealtimeLog(message) {
    const logDiv = document.getElementById('realtimeLog');
    if (!logDiv) return;
    
    const timestamp = new Date().toLocaleTimeString('th-TH');
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = `[${timestamp}] ${message}`;
    
    logDiv.insertBefore(entry, logDiv.firstChild);
    
    // Keep only last 20 entries
    while (logDiv.children.length > 20) {
        logDiv.removeChild(logDiv.lastChild);
    }
}

function updateGateStatus(isOpen) {
    const statusEl = document.getElementById('gateConnectionStatus');
    if (statusEl) {
        statusEl.textContent = isOpen ? 'Open' : 'Closed';
        statusEl.className = isOpen ? 'status-badge connected' : 'status-badge disconnected';
    }
}

// ===== Authentication =====
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            sessionToken = data.session_token;
            localStorage.setItem('session_token', sessionToken);
            currentUser = data.user;
            updateUserUI();
            showNotification('Login successful!', 'success');
        } else {
            showError('loginError', data.message);
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('loginError', 'Login failed');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;
    
    if (password !== confirmPassword) {
        showError('registerError', 'Passwords do not match');
        return;
    }
    
    const formData = new FormData();
    formData.append('username', username);
    formData.append('email', email);
    formData.append('password', password);
    formData.append('confirm_password', confirmPassword);
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('registerSuccess', data.message);
            setTimeout(() => {
                document.getElementById('registerModal').classList.remove('active');
                document.getElementById('loginModal').classList.add('active');
            }, 2000);
        } else {
            showError('registerError', data.message);
        }
    } catch (error) {
        console.error('Register error:', error);
        showError('registerError', 'Registration failed');
    }
}

async function handleLogout() {
    if (sessionToken) {
        const formData = new FormData();
        formData.append('session_token', sessionToken);
        
        await fetch('/api/auth/logout', {
            method: 'POST',
            body: formData
        });
    }
    
    localStorage.removeItem('session_token');
    sessionToken = null;
    currentUser = null;
    
    // Hide admin tabs
    document.querySelectorAll('.admin-only').forEach(el => {
        el.style.display = 'none';
    });
    
    showLoginModal();
    showNotification('Logged out successfully', 'info');
}

// ===== Utility Functions =====
function showNotification(message, type = 'info') {
    // Simple notification (can be replaced with toast library)
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        info: '#3b82f6',
        warning: '#f59e0b'
    };
    
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${colors[type]};
        color: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
        max-width: 300px;
        font-weight: 500;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.style.display = 'block';
        setTimeout(() => el.style.display = 'none', 5000);
    }
}

function showSuccess(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) {
        el.textContent = message;
        el.style.display = 'block';
    }
}

function showImageModal(imageSrc) {
    // Create modal to show full image
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
        cursor: pointer;
    `;
    
    const img = document.createElement('img');
    img.src = imageSrc;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    `;
    
    modal.appendChild(img);
    modal.addEventListener('click', () => modal.remove());
    document.body.appendChild(modal);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(100px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100px);
        }
    }
    
    @keyframes flash {
        0%, 100% {
            background: transparent;
        }
        50% {
            background: rgba(16, 185, 129, 0.2);
        }
    }
    
    .camera-detection-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 4px solid var(--primary-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 14px;
    }
    
    .detection-plate {
        font-weight: 700;
        font-size: 16px;
        color: var(--primary-color);
    }
    
    .detection-time {
        font-size: 12px;
        color: var(--text-light);
    }
    
    #cameraPreview {
        width: 100%;
        max-width: 640px;
        border-radius: 12px;
        border: 2px solid var(--border-color);
        margin: 20px auto;
        display: block;
    }
    
    #cameraSection {
        text-align: center;
    }
    
    #cameraDetections {
        max-height: 400px;
        overflow-y: auto;
        margin-top: 20px;
    }
`;
document.head.appendChild(style);

console.log('✅ App initialized');

