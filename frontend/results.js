document.addEventListener('DOMContentLoaded', () => {
    // ---- AUTHENTICATION CHECK ----
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }

    // Logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            localStorage.clear();
            sessionStorage.clear();
            window.location.href = '/login.html';
        });
    }
    // ------------------------------

    // Load initial prediction results from session storage
    const resultsStr = sessionStorage.getItem('predictionResults');
    if (!resultsStr) {
        alert("No recent prediction found. Redirecting to upload page.");
        window.location.href = '/index.html';
        return;
    }

    const data = JSON.parse(resultsStr);
    const req_id = data.req_id;

    // Elements
    const originalImg = document.getElementById('original-image');
    const defectsList = document.getElementById('defects-list');
    
    const generateBtn = document.getElementById('generate-xai-btn');
    const btnText = document.getElementById('xai-btn-text');
    const btnLoader = document.getElementById('xai-loader');
    
    const xaiContainer = document.getElementById('xai-results-container');
    const xaiImg = document.getElementById('xai-image');
    const expText = document.getElementById('ai-explanation-text');
    const reportBox = document.getElementById('xai-report-box');

    // Display Initial Detections
    const t = new Date().getTime();
    originalImg.src = `${data.original_image_path}?t=${t}`;

    if (data.detections.length === 0) {
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
                <div class="defect-item ${urgencyClass}" style="background: rgba(255, 255, 255, 0.05); border-left: 4px solid var(--primary); padding: 1rem; margin-bottom: 1rem; border-radius: 4px;">
                    <div class="defect-header" style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span class="defect-title" style="font-weight: bold; font-size: 1.1rem; text-transform: capitalize;">${d.class_name}</span>
                        <span class="defect-confidence" style="background: rgba(255, 255, 255, 0.1); padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.9rem;">${Math.round(d.confidence * 100)}%</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.95rem; color: var(--text-muted);">
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

    // Handle XAI Generation
    generateBtn.addEventListener('click', async () => {
        // UI Updates
        generateBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'block';

        try {
            const response = await fetch('/api/explain', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ req_id: req_id })
            });

            if (!response.ok) {
                if (response.status === 401) {
                    localStorage.clear();
                    window.location.href = '/login.html';
                    return;
                }
                const err = await response.json();
                throw new Error(err.detail || 'XAI generation failed');
            }

            const xaiData = await response.json();
            
            // Populate XAI results
            const t2 = new Date().getTime();
            xaiImg.src = `${xaiData.explanation_path}?t=${t2}`;
            expText.textContent = xaiData.explanation;

            // Fetch Text Report
            if (xaiData.report_path) {
                try {
                    const res = await fetch(`${xaiData.report_path}?t=${t2}`);
                    const text = await res.text();
                    reportBox.textContent = text;
                } catch (err) {
                    reportBox.textContent = "Failed to load the detailed text report.";
                }
            } else {
                reportBox.textContent = "No detailed report generated.";
            }

            // Show container
            xaiContainer.style.display = 'flex';

            // Hide the button container or change button state
            generateBtn.parentElement.style.display = 'none';
            
            // Scroll to XAI results smoothly
            setTimeout(() => {
                xaiContainer.scrollIntoView({ behavior: 'smooth' });
            }, 100);

        } catch (err) {
            alert(err.message);
            generateBtn.disabled = false;
            btnText.style.display = 'block';
            btnLoader.style.display = 'none';
        }
    });
});
