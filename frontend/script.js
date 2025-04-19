// Konfigurasi
const BACKEND_URL = 'http://10.108.206.227:3001'; // Ganti dengan IP Termux atau URL ngrok

// Elemen UI
const searchBtn = document.getElementById('search-btn');
const searchInput = document.getElementById('search-input');
const resultsDiv = document.getElementById('results');
const loadingDiv = document.getElementById('loading');

// Event Listeners
searchBtn.addEventListener('click', searchVideos);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchVideos();
});

// Fungsi Pencarian
async function searchVideos() {
    const query = searchInput.value.trim();
    if (!query) return showToast('Masukkan kata kunci pencarian!', 'danger');

    try {
        showLoading(true);
        clearResults();
        
        const response = await fetch(`${BACKEND_URL}/api/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Gagal mengambil data');
        
        const videos = await response.json();
        if (videos.error) throw new Error(videos.error);
        if (videos.length === 0) throw new Error('Tidak ada hasil ditemukan');

        displayResults(videos);
    } catch (error) {
        showToast(error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

// Tampilkan Hasil
function displayResults(videos) {
    resultsDiv.innerHTML = videos.map(video => `
        <div class="col-md-6 col-lg-4">
            <div class="card video-card shadow-sm">
                <img src="${video.thumbnail}" class="video-thumbnail" alt="${video.title}">
                <div class="card-body">
                    <h5 class="card-title">${video.title}</h5>
                    <p class="text-muted">
                        <i class="bi bi-person"></i> ${video.author} 
                        <br>
                        <i class="bi bi-clock"></i> ${video.duration}
                    </p>
                    <div class="d-grid gap-2">
                        <button class="btn btn-danger btn-download" 
                                data-url="${video.url}" data-format="mp4">
                            <i class="bi bi-file-earmark-play"></i> Download MP4
                        </button>
                        <button class="btn btn-outline-danger btn-download" 
                                data-url="${video.url}" data-format="mp3">
                            <i class="bi bi-music-note"></i> Download MP3
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');

    // Tambahkan event listener untuk tombol download
    document.querySelectorAll('.btn-download').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const url = e.target.dataset.url;
            const format = e.target.dataset.format;
            downloadVideo(url, format);
        });
    });
}

// Fungsi Download
function downloadVideo(url, format) {
    showToast(`Memulai download ${format.toUpperCase()}...`, 'info');
    window.open(`${BACKEND_URL}/api/download?url=${encodeURIComponent(url)}&format=${format}`, '_blank');
}

// Helper Functions
function showLoading(show) {
    loadingDiv.style.display = show ? 'block' : 'none';
}

function clearResults() {
    resultsDiv.innerHTML = '';
}

function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    const toastId = `toast-${Date.now()}`;
    const bgColor = type === 'danger' ? 'bg-danger' : 'bg-primary';
    
    toastContainer.innerHTML += `
        <div id="${toastId}" class="toast show align-items-center text-white ${bgColor} border-0">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${type === 'danger' ? 'bi-exclamation-triangle' : 'bi-info-circle'}"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;

    setTimeout(() => {
        const toast = document.getElementById(toastId);
        if (toast) toast.remove();
    }, 3000);
}

// Inisialisasi tooltip Bootstrap
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
tooltipTriggerList.map(tooltipTriggerEl => {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});
