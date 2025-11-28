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
let cameraSource = 'webrtc'; // 'webrtc' or 'droidcam'
let droidcamURL = null;

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
        
        // Show/hide UI based on role
        if (currentUser.role === 'admin') {
            // Admin: Show all features
            document.querySelectorAll('.admin-only').forEach(el => {
                el.style.display = 'block';
            });
            document.getElementById('userUploadSection').style.display = 'none';
            document.getElementById('adminUploadSection').style.display = 'block';
            document.getElementById('fileInputAdmin').style.display = 'block';
            document.getElementById('fileInput').style.display = 'none';
            
            // Load admin-specific data
            loadPlateStatus();
        } else {
            // User: Show only image upload
            document.querySelectorAll('.admin-only').forEach(el => {
                if (!el.classList.contains('admin-tab')) { // Keep admin tab button hidden
                    el.style.display = 'none';
                }
            });
            document.getElementById('userUploadSection').style.display = 'block';
            document.getElementById('adminUploadSection').style.display = 'none';
            document.getElementById('fileInputAdmin').style.display = 'none';
            document.getElementById('fileInput').style.display = 'block';
            
            // Make file input accept only images for users
            const userInput = document.getElementById('fileInput');
            if (userInput) {
                userInput.accept = 'image/*';
            }
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
    const fileInputAdmin = document.getElementById('fileInputAdmin');
    
    uploadArea.addEventListener('click', () => {
        // Use admin input if admin, user input if user
        const activeInput = (currentUser && currentUser.role === 'admin') ? fileInputAdmin : fileInput;
        if (activeInput) activeInput.click();
    });
    
    if (fileInput) fileInput.addEventListener('change', handleFileSelect);
    if (fileInputAdmin) fileInputAdmin.addEventListener('change', handleFileSelect);
    
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
    
    // Camera source selection
    document.querySelectorAll('input[name="cameraSource"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            cameraSource = e.target.value;
            const droidcamSettings = document.getElementById('droidcamSettings');
            if (cameraSource === 'droidcam') {
                droidcamSettings.style.display = 'block';
                updateDroidcamURL();
            } else {
                droidcamSettings.style.display = 'none';
            }
            // Stop camera if active
            if (isCameraActive) {
                stopCamera();
            }
        });
    });
    
    // DroidCam IP/Port input handlers
    document.getElementById('droidcamIP')?.addEventListener('input', updateDroidcamURL);
    document.getElementById('droidcamPort')?.addEventListener('input', updateDroidcamURL);
    
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
        loadPlateStatus();
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
        cameraSource = document.querySelector('input[name="cameraSource"]:checked')?.value || 'webrtc';
        
        if (cameraSource === 'droidcam') {
            // Start DroidCam IP camera
            await startDroidcam();
        } else {
            // Start WebRTC camera
            await startWebRTCCamera();
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
        isCameraActive = false;
    }
}

async function startWebRTCCamera() {
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
    const droidcamPreview = document.getElementById('droidcamPreview');
    
    if (videoPreview) {
        videoPreview.srcObject = cameraStream;
        videoPreview.play();
        videoPreview.style.display = 'block';
    }
    
    if (droidcamPreview) {
        droidcamPreview.style.display = 'none';
    }
}

async function startDroidcam() {
    // Get DroidCam settings
    const ip = document.getElementById('droidcamIP')?.value || '192.168.100.143';
    const port = document.getElementById('droidcamPort')?.value || '4747';
    droidcamURL = `http://${ip}:${port}/mjpegfeed`;
    
    // Show DroidCam preview
    const videoPreview = document.getElementById('cameraPreview');
    const droidcamPreview = document.getElementById('droidcamPreview');
    
    if (videoPreview) {
        videoPreview.style.display = 'none';
    }
    
    if (droidcamPreview) {
        droidcamPreview.src = droidcamURL;
        droidcamPreview.style.display = 'block';
        droidcamPreview.onerror = () => {
            showNotification('Failed to connect to DroidCam. Check IP and Port.', 'error');
            stopCamera();
        };
    }
    
    // Test connection
    try {
        const testResponse = await fetch(droidcamURL, { method: 'HEAD', mode: 'no-cors' });
        console.log('DroidCam URL:', droidcamURL);
    } catch (error) {
        console.warn('DroidCam connection test:', error);
        // Continue anyway, the img tag will show error if it fails
    }
}

function updateDroidcamURL() {
    const ip = document.getElementById('droidcamIP')?.value || '192.168.100.143';
    const port = document.getElementById('droidcamPort')?.value || '4747';
    const urlDisplay = document.getElementById('droidcamURL');
    if (urlDisplay) {
        urlDisplay.textContent = `http://${ip}:${port}/mjpegfeed`;
    }
}

function stopCamera() {
    // Stop camera stream (WebRTC)
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    // Stop DroidCam preview
    const droidcamPreview = document.getElementById('droidcamPreview');
    if (droidcamPreview) {
        droidcamPreview.src = '';
        droidcamPreview.style.display = 'none';
    }
    
    // Stop video preview
    const videoPreview = document.getElementById('cameraPreview');
    if (videoPreview) {
        videoPreview.srcObject = null;
        videoPreview.style.display = 'none';
    }
    
    // Stop auto-capture
    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
    
    isCameraActive = false;
    droidcamURL = null;
    
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
        if (cameraSource === 'droidcam' && droidcamURL) {
            // Use DroidCam IP camera - send URL to backend
            await processDroidcamFrame();
        } else {
            // Use WebRTC camera - capture from video element
            await processWebRTCFrame();
        }
    } catch (error) {
        console.error('Capture error:', error);
    }
}

async function processWebRTCFrame() {
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
}

async function processDroidcamFrame() {
    // For DroidCam, we send the URL to backend instead of capturing frame
    // Backend will fetch the frame from the IP camera using cv2.VideoCapture
    
    // Use the base URL (no timestamp needed for MJPEG stream)
    try {
        const formData = new FormData();
        formData.append('image_url', droidcamURL);
        
        const response = await fetch('/detect', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            console.error('Detection API error:', errorData);
            return;
        }
        
        const result = await response.json();
        
        if (result.plate_text) {
            // Show detection in UI
            showCameraDetection(result);
            
            // Flash preview on detection
            const droidcamPreview = document.getElementById('droidcamPreview');
            if (droidcamPreview) {
                highlightDetection(droidcamPreview, null);
            }
        }
        
    } catch (error) {
        console.error('DroidCam detection error:', error);
        showNotification('DroidCam detection failed: ' + error.message, 'error');
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

function highlightDetection(element, ctx) {
    // Flash border on video or image element
    if (element) {
        const originalBorder = element.style.border;
        element.style.border = '4px solid #10b981';
        element.style.transition = 'border 0.3s ease';
        setTimeout(() => {
            element.style.border = originalBorder || '2px solid #e2e8f0';
        }, 500);
    }
}

// ===== File Upload =====
function handleFileSelect() {
    // Get the active file input (admin or user)
    const activeInput = (currentUser && currentUser.role === 'admin' && document.getElementById('fileInputAdmin')) 
        ? document.getElementById('fileInputAdmin') 
        : document.getElementById('fileInput');
    
    const file = activeInput?.files[0];
    
    if (!file) return;
    
    // Show preview
    const preview = document.getElementById('preview');
    const imagePreview = document.getElementById('imagePreview');
    const videoPreview = document.getElementById('videoPreview');
    const videoPlayerSection = document.getElementById('videoPlayerSection');
    const videoPlayer = document.getElementById('videoPlayer');
    
    preview.style.display = 'block';
    
    if (file.type.startsWith('image/')) {
        imagePreview.src = URL.createObjectURL(file);
        imagePreview.style.display = 'block';
        videoPreview.style.display = 'none';
        if (videoPlayerSection) videoPlayerSection.style.display = 'none';
        
        // Show upload button for images
        document.getElementById('uploadBtn').style.display = 'inline-block';
        
    } else if (file.type.startsWith('video/') && currentUser && currentUser.role === 'admin') {
        // Admin only: Video playback with real-time detection
        const videoURL = URL.createObjectURL(file);
        
        // Show video player
        if (videoPlayerSection) videoPlayerSection.style.display = 'block';
        if (videoPlayer) {
            videoPlayer.src = videoURL;
            
            // Start video detection when video plays
            videoPlayer.onloadedmetadata = () => {
                startVideoDetection(videoPlayer);
            };
        }
        
        videoPreview.style.display = 'none';
        imagePreview.style.display = 'none';
        
        // Don't show upload button for videos (we detect while playing)
        document.getElementById('uploadBtn').style.display = 'none';
    }
    
    // Hide result
    document.getElementById('result').style.display = 'none';
}

// Video detection state
let videoDetectionActive = false;
let videoDetectionInterval = null;

function startVideoDetection(videoElement) {
    if (videoDetectionActive) return;
    
    videoDetectionActive = true;
    const detectionList = document.getElementById('videoDetectionList');
    if (detectionList) detectionList.innerHTML = '';
    
    showNotification('Starting video detection...', 'info');
    
    // Detect every 2 seconds while video is playing
    videoDetectionInterval = setInterval(async () => {
        if (videoElement.paused || videoElement.ended) {
            stopVideoDetection();
            return;
        }
        
        // Capture current frame
        const canvas = document.createElement('canvas');
        canvas.width = videoElement.videoWidth;
        canvas.height = videoElement.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(videoElement, 0, 0);
        
        // Convert to blob and send to API
        canvas.toBlob(async (blob) => {
            if (blob) {
                try {
                    const formData = new FormData();
                    formData.append('file', blob, 'video_frame.jpg');
                    
                    const response = await fetch('/detect', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.plate_text) {
                        showVideoDetection(result, detectionList, videoElement.currentTime);
                    }
                } catch (error) {
                    console.error('Video detection error:', error);
                }
            }
        }, 'image/jpeg', 0.8);
    }, 2000);
    
    // Stop detection when video ends
    videoElement.addEventListener('ended', stopVideoDetection);
    videoElement.addEventListener('pause', () => {
        if (videoElement.paused && !videoElement.ended) {
            stopVideoDetection();
        }
    });
}

function stopVideoDetection() {
    if (videoDetectionInterval) {
        clearInterval(videoDetectionInterval);
        videoDetectionInterval = null;
    }
    videoDetectionActive = false;
}

function showVideoDetection(result, container, timestamp) {
    if (!container) return;
    
    const detectionDiv = document.createElement('div');
    detectionDiv.style.cssText = `
        padding: 12px;
        margin-bottom: 8px;
        background: ${result.is_new_plate ? '#e0f2fe' : '#fef3c7'};
        border-left: 4px solid ${result.is_new_plate ? '#0369a1' : '#f59e0b'};
        border-radius: 8px;
    `;
    
    const statusBadge = result.is_new_plate 
        ? '<span style="background: #10b981; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">🆕 NEW</span>'
        : '<span style="background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">🔄 DUPLICATE</span>';
    
    const timeFormatted = formatTime(timestamp);
    
    detectionDiv.innerHTML = `
        ${statusBadge}
        <div style="font-weight: bold; margin-top: 5px; font-size: 16px;">${result.plate_text || 'N/A'}</div>
        <div style="color: #6b7280; font-size: 14px;">${result.province_text || ''}</div>
        <div style="color: #6b7280; font-size: 12px; margin-top: 5px;">
            Time: ${timeFormatted} | Confidence: ${((result.confidence || 0) * 100).toFixed(1)}%
        </div>
    `;
    
    container.insertBefore(detectionDiv, container.firstChild);
    
    // Keep only last 20 detections
    while (container.children.length > 20) {
        container.removeChild(container.lastChild);
    }
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

async function processUpload() {
    // Get the active file input (admin or user)
    const activeInput = (currentUser && currentUser.role === 'admin' && document.getElementById('fileInputAdmin')) 
        ? document.getElementById('fileInputAdmin') 
        : document.getElementById('fileInput');
    
    const file = activeInput?.files[0];
    
    if (!file) {
        showNotification('Please select a file', 'error');
        return;
    }
    
    // Users can only upload images
    if (currentUser && currentUser.role !== 'admin' && !file.type.startsWith('image/')) {
        showNotification('Users can only upload image files', 'error');
        return;
    }
    
    // Show loading
    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').style.display = 'none';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        // Choose endpoint based on file type (only for admin)
        const endpoint = (currentUser && currentUser.role === 'admin' && file.type.startsWith('video/')) 
            ? '/detect-video' 
            : '/detect';
        
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
        
        // Refresh plate status if admin
        if (currentUser && currentUser.role === 'admin') {
            loadPlateStatus();
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
    
    // Show plate status (new or duplicate) for admin
    const gateStatusEl = document.getElementById('gateStatus');
    if (gateStatusEl && currentUser && currentUser.role === 'admin') {
        if (result.is_new_plate) {
            gateStatusEl.innerHTML = '<span style="color: #10b981;">🆕 ป้ายใหม่</span>';
        } else {
            gateStatusEl.innerHTML = `<span style="color: #f59e0b;">🔄 ป้ายซ้ำ (เจอแล้ว ${result.seen_count || 1} ครั้ง)</span>`;
        }
    } else if (gateStatusEl) {
        gateStatusEl.textContent = result.gate_opened ? '✅ Opened' : '❌ Not Opened';
    }
    
    const message = result.is_new_plate ? '🆕 Detection completed! New plate detected!' : '🔄 Detection completed! Duplicate plate.';
    showNotification(message, result.is_new_plate ? 'success' : 'info');
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
        
        // Also load plate status
        await loadPlateStatus();
        
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function loadPlateStatus() {
    try {
        const response = await fetch('/api/plates/status');
        const data = await response.json();
        
        // Update counts
        document.getElementById('newPlatesCount').textContent = data.new_plates_count || 0;
        document.getElementById('duplicatePlatesCount').textContent = data.duplicate_plates_count || 0;
        document.getElementById('totalPlatesCount').textContent = data.total_unique_plates || 0;
        
        // Display new plates
        const newPlatesList = document.getElementById('newPlatesList');
        if (newPlatesList) {
            if (data.new_plates && data.new_plates.length > 0) {
                newPlatesList.innerHTML = data.new_plates.map(plate => `
                    <div class="plate-card" style="padding: 15px; margin-bottom: 10px; background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%); border-left: 4px solid #0369a1; border-radius: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <div style="font-weight: bold; font-size: 18px; color: #0369a1;">${plate.plate_text || 'N/A'}</div>
                                <div style="color: #6b7280; margin-top: 5px;">${plate.province_text || ''}</div>
                                <div style="color: #6b7280; font-size: 12px; margin-top: 5px;">
                                    Confidence: ${((plate.confidence || 0) * 100).toFixed(1)}% | 
                                    ${plate.created_at ? new Date(plate.created_at).toLocaleString('th-TH') : ''}
                                </div>
                            </div>
                            ${plate.plate_image ? `
                                <img src="${plate.plate_image}" style="width: 80px; height: 50px; object-fit: cover; border-radius: 6px; margin-left: 15px;" onclick="showImageModal('${plate.plate_image}')">
                            ` : ''}
                        </div>
                    </div>
                `).join('');
            } else {
                newPlatesList.innerHTML = '<p class="text-center" style="color: var(--text-light);">ไม่มีป้ายใหม่</p>';
            }
        }
        
        // Display duplicate plates
        const duplicatePlatesList = document.getElementById('duplicatePlatesList');
        if (duplicatePlatesList) {
            if (data.duplicate_plates && data.duplicate_plates.length > 0) {
                duplicatePlatesList.innerHTML = data.duplicate_plates.map(plate => `
                    <div class="plate-card" style="padding: 15px; margin-bottom: 10px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #f59e0b; border-radius: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                                        เจอแล้ว ${plate.seen_count || 1} ครั้ง
                                    </span>
                                </div>
                                <div style="font-weight: bold; font-size: 18px; color: #92400e; margin-top: 5px;">${plate.plate_text || 'N/A'}</div>
                                <div style="color: #6b7280; margin-top: 5px;">${plate.province_text || ''}</div>
                                <div style="color: #6b7280; font-size: 12px; margin-top: 5px;">
                                    Confidence: ${((plate.confidence || 0) * 100).toFixed(1)}% | 
                                    ${plate.created_at ? new Date(plate.created_at).toLocaleString('th-TH') : ''}
                                </div>
                            </div>
                            ${plate.plate_image ? `
                                <img src="${plate.plate_image}" style="width: 80px; height: 50px; object-fit: cover; border-radius: 6px; margin-left: 15px;" onclick="showImageModal('${plate.plate_image}')">
                            ` : ''}
                        </div>
                    </div>
                `).join('');
            } else {
                duplicatePlatesList.innerHTML = '<p class="text-center" style="color: var(--text-light);">ไม่มีป้ายซ้ำ</p>';
            }
        }
        
    } catch (error) {
        console.error('Failed to load plate status:', error);
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

