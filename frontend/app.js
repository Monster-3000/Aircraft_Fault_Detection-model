document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loader = document.getElementById('loader');
    const resultsContainer = document.getElementById('results-container');
    const originalImg = document.getElementById('original-image');
    const xaiImg = document.getElementById('xai-image');
    const defectsList = document.getElementById('defects-list');
    
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
        if(e.dataTransfer.files.length) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    // Handle Click upload
    fileInput.addEventListener('change', (e) => {
        if(e.target.files.length) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        if(!file.type.startsWith('image/')) {
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
        resultsContainer.classList.remove('active');
    }

    analyzeBtn.addEventListener('click', async () => {
        if(!selectedFile) return;

        // UI updates during fetch
        analyzeBtn.style.display = 'none';
        loader.style.display = 'block';
        resultsContainer.classList.remove('active');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                body: formData
            });

            if(!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Analysis failed');
            }

            const data = await response.json();
            displayResults(data);
            
        } catch(err) {
            alert(err.message);
        } finally {
            analyzeBtn.style.display = 'block';
            loader.style.display = 'none';
        }
    });

    function displayResults(data) {
        // Set images with a timestamp query param to bypass cache
        const t = new Date().getTime();
        originalImg.src = `${data.original_image_path}?t=${t}`;
        xaiImg.src = `${data.explanation_path}?t=${t}`;
        
        // Ensure there is an explanation element
        let expEl = document.getElementById('ai-explanation-text');
        if(!expEl) {
            expEl = document.createElement('div');
            expEl.id = 'ai-explanation-text';
            expEl.style.marginTop = '1rem';
            expEl.style.padding = '1rem';
            expEl.style.background = 'rgba(16, 185, 129, 0.1)';
            expEl.style.borderLeft = '4px solid var(--accent)';
            expEl.style.borderRadius = '0 8px 8px 0';
            expEl.style.color = 'var(--text-main)';
            // Insert it under the xai-image container
            xaiImg.parentElement.parentElement.appendChild(expEl);
        }
        expEl.textContent = data.explanation;

        // Fetch and display the text report
        const reportBox = document.getElementById('xai-report-box');
        if (data.report_path) {
            reportBox.textContent = "Loading report...";
            fetch(`${data.report_path}?t=${t}`)
                .then(res => res.text())
                .then(text => {
                    reportBox.textContent = text;
                })
                .catch(err => {
                    reportBox.textContent = "Failed to load the XAI report.";
                });
        } else {
            reportBox.textContent = "No XAI report generated for this image.";
        }

        // Build defects list
        defectsList.innerHTML = '';
        
        if(data.detections.length === 0) {
            defectsList.innerHTML = `
                <div style="text-align: center; color: var(--accent); padding: 2rem;">
                    <h3>No defects detected</h3>
                    <p>The surface appears clear.</p>
                </div>
            `;
        } else {
            data.detections.forEach(d => {
                const urgencyClass = d.urgency.toLowerCase();
                const html = `
                    <div class="defect-item ${urgencyClass}">
                        <div class="defect-header">
                            <span class="defect-title">${d.class_name}</span>
                            <span class="defect-confidence">${Math.round(d.confidence * 100)}%</span>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 0.5rem; font-size: 0.95rem; color: var(--text-muted);">
                            <div><strong>Severity:</strong> ${d.severity}/100</div>
                            <div><strong>Urgency:</strong> ${d.urgency}</div>
                        </div>
                        <div style="margin-top: 1rem; color: var(--text-main);">
                            <strong>Recommendation:</strong> ${d.recommendation}
                        </div>
                    </div>
                `;
                defectsList.insertAdjacentHTML('beforeend', html);
            });
        }

        resultsContainer.classList.add('active');
    }
});
