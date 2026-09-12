document.addEventListener('DOMContentLoaded', () => {
    // ---- AUTHENTICATION CHECK ----
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login.html';
        return; // Stop execution
    }

    // Load user info
    const username = localStorage.getItem('username');
    const role = localStorage.getItem('role');
    const userEl = document.getElementById('current-user');
    const roleEl = document.getElementById('current-role');
    if (userEl) userEl.textContent = username;
    if (roleEl) roleEl.textContent = role;

    // Logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.clear();
            window.location.href = '/login.html';
        });
    }
    // ------------------------------

    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loader = document.getElementById('loader');


    let selectedFile = null;

    // Handle Drag and Drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    // Handle Click upload
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            return;
        }
        selectedFile = file;

        // Update UI to show selected file
        const content = dropzone.querySelector('.upload-content');
        content.innerHTML = `
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--accent); margin-bottom: 1rem;">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <h3 style="margin-bottom: 0.5rem; color: var(--accent);">${file.name}</h3>
            <p style="color: var(--text-muted); font-size: 0.9rem;">Ready to analyze</p>
        `;

        analyzeBtn.disabled = false;
    }

    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // UI updates during fetch
        analyzeBtn.style.display = 'none';
        loader.style.display = 'block';


        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}` // Passing token for security
                },
                body: formData
            });

            if (!response.ok) {
                // if unauthorized
                if (response.status === 401) {
                    localStorage.clear();
                    window.location.href = '/login.html';
                    return;
                }
                const err = await response.json();
                throw new Error(err.detail || 'Analysis failed');
            }

            const data = await response.json();
            
            // Save results to session storage for the results page
            sessionStorage.setItem('predictionResults', JSON.stringify(data));
            
            // Redirect to the new results page
            window.location.href = '/results.html';

        } catch (err) {
            alert(err.message);
        } finally {
            analyzeBtn.style.display = 'block';
            loader.style.display = 'none';
        }
    });


});
