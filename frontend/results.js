const API_BASE_URL = (window.location.protocol === 'file:' || (window.location.port && window.location.port !== '8000')) ? 'http://127.0.0.1:8000' : '';

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
    originalImg.src = `${API_BASE_URL}${data.original_image_path}?t=${t}`;

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

    // Initialize the 3D Aircraft Model
    if (typeof THREE !== 'undefined') {
        init3DAircraft(data.detections);
    }

    // Handle XAI Generation
    generateBtn.addEventListener('click', async () => {
        // UI Updates
        generateBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'block';

        try {
            const response = await fetch(`${API_BASE_URL}/api/explain`, {
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
            xaiImg.src = `${API_BASE_URL}${xaiData.explanation_path}?t=${t2}`;
            expText.textContent = xaiData.explanation;

            // Fetch Text Report
            if (xaiData.report_path) {
                try {
                    const res = await fetch(`${API_BASE_URL}${xaiData.report_path}?t=${t2}`);
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

    // --- 3D Aircraft rendering logic ---
    function init3DAircraft(detections) {
        const container = document.getElementById('threejs-container');
        if (!container) return;

        // Scene setup
        const scene = new THREE.Scene();
        scene.background = null; // transparent to show css background
        
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
        // Position camera perfectly top-down to match the reference image
        camera.position.set(0, 80, 0);
        camera.up.set(0, 0, -1);

        const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.autoRotate = false;
        controls.autoRotateSpeed = 1.0;

        // Wireframe material mimicking the reference image
        const wireMaterial = new THREE.MeshBasicMaterial({ 
            color: 0xffffff, 
            wireframe: true,
            transparent: true,
            opacity: 0.4
        });

        const airplane = new THREE.Group();

        // 1. Fuselage (Sphere stretched along Z)
        const fuselageGeo = new THREE.SphereGeometry(2.5, 32, 32);
        fuselageGeo.scale(1, 1, 11);
        const fuselage = new THREE.Mesh(fuselageGeo, wireMaterial);
        airplane.add(fuselage);

        // 2. Wings (Swept back BoxGeometry)
        const wingGeo = new THREE.BoxGeometry(45, 0.5, 12, 20, 1, 8);
        const pos = wingGeo.attributes.position;
        for (let i = 0; i < pos.count; i++) {
            const x = pos.getX(i);
            let z = pos.getZ(i);
            const taper = 1 - (Math.abs(x) / 22.5) * 0.5;
            z = z * taper;
            z -= Math.abs(x) * 0.6;
            pos.setZ(i, z);
        }
        wingGeo.computeVertexNormals();
        const wings = new THREE.Mesh(wingGeo, wireMaterial);
        wings.position.set(0, 0, 2);
        airplane.add(wings);

        // 3. Engines (4 under wings)
        const engineGeo = new THREE.CylinderGeometry(0.8, 0.8, 4, 16, 4);
        engineGeo.rotateX(Math.PI / 2);
        
        const e1 = new THREE.Mesh(engineGeo, wireMaterial); e1.position.set(10, -1.5, 0);
        const e2 = new THREE.Mesh(engineGeo, wireMaterial); e2.position.set(16, -1.5, -4);
        const e3 = new THREE.Mesh(engineGeo, wireMaterial); e3.position.set(-10, -1.5, 0);
        const e4 = new THREE.Mesh(engineGeo, wireMaterial); e4.position.set(-16, -1.5, -4);
        airplane.add(e1, e2, e3, e4);

        // 4. Horizontal Stabilizers (Tail wings)
        const hStabGeo = new THREE.BoxGeometry(16, 0.5, 5, 10, 1, 4);
        const hPos = hStabGeo.attributes.position;
        for (let i = 0; i < hPos.count; i++) {
            const x = hPos.getX(i);
            let z = hPos.getZ(i);
            const taper = 1 - (Math.abs(x) / 8) * 0.5;
            z = z * taper;
            z -= Math.abs(x) * 0.6;
            hPos.setZ(i, z);
        }
        hStabGeo.computeVertexNormals();
        const hStab = new THREE.Mesh(hStabGeo, wireMaterial);
        hStab.position.set(0, 0, -22);
        airplane.add(hStab);

        // 5. Vertical Stabilizer (Tail fin)
        const vStabGeo = new THREE.BoxGeometry(0.5, 12, 8, 1, 6, 4);
        const vPos = vStabGeo.attributes.position;
        for (let i = 0; i < vPos.count; i++) {
            const y = vPos.getY(i);
            let z = vPos.getZ(i);
            const normY = (y + 6) / 12; // 0 at base, 1 at tip
            const taper = 1 - normY * 0.6;
            z = z * taper;
            z -= normY * 6;
            vPos.setZ(i, z);
        }
        vStabGeo.computeVertexNormals();
        const vStab = new THREE.Mesh(vStabGeo, wireMaterial);
        vStab.position.set(0, 7, -21);
        airplane.add(vStab);

        // 6. Landing Gear (Wheels)
        const wheelGeo = new THREE.CylinderGeometry(0.6, 0.6, 0.4, 12);
        wheelGeo.rotateZ(Math.PI / 2); // Stand tires upright

        // Nose gear
        const noseWheel1 = new THREE.Mesh(wheelGeo, wireMaterial); noseWheel1.position.set(0.4, -3, 20);
        const noseWheel2 = new THREE.Mesh(wheelGeo, wireMaterial); noseWheel2.position.set(-0.4, -3, 20);
        
        // Main gear (left)
        const mlWheel1 = new THREE.Mesh(wheelGeo, wireMaterial); mlWheel1.position.set(4.2, -3.5, 0);
        const mlWheel2 = new THREE.Mesh(wheelGeo, wireMaterial); mlWheel2.position.set(5.2, -3.5, 0);
        const mlWheel3 = new THREE.Mesh(wheelGeo, wireMaterial); mlWheel3.position.set(4.2, -3.5, -1.5);
        const mlWheel4 = new THREE.Mesh(wheelGeo, wireMaterial); mlWheel4.position.set(5.2, -3.5, -1.5);

        // Main gear (right)
        const mrWheel1 = new THREE.Mesh(wheelGeo, wireMaterial); mrWheel1.position.set(-4.2, -3.5, 0);
        const mrWheel2 = new THREE.Mesh(wheelGeo, wireMaterial); mrWheel2.position.set(-5.2, -3.5, 0);
        const mrWheel3 = new THREE.Mesh(wheelGeo, wireMaterial); mrWheel3.position.set(-4.2, -3.5, -1.5);
        const mrWheel4 = new THREE.Mesh(wheelGeo, wireMaterial); mrWheel4.position.set(-5.2, -3.5, -1.5);

        airplane.add(noseWheel1, noseWheel2, mlWheel1, mlWheel2, mlWheel3, mlWheel4, mrWheel1, mrWheel2, mrWheel3, mrWheel4);

        scene.add(airplane);

        // Add Defect Highlights
        const defectMat = new THREE.MeshBasicMaterial({ color: 0xff0000, transparent: true, opacity: 0.7 });
        const highlightGeo = new THREE.SphereGeometry(3.5, 16, 16);
        
        detections.forEach((d, index) => {
            const loc = d.location || "";
            const highlight = new THREE.Mesh(highlightGeo, defectMat);
            
            // Map location to 3D coordinates
            if (loc.includes("Nose") || loc.includes("Radome") || loc.includes("Cockpit")) {
                highlight.position.set(0, 0, 25);
            } else if (loc.includes("Wings") || loc.includes("Engine")) {
                // Alternate left and right wings if multiple
                if (index % 2 === 0) {
                    highlight.position.set(15, 0, -2);
                } else {
                    highlight.position.set(-15, 0, -2);
                }
            } else if (loc.includes("Empennage") || loc.includes("Tail")) {
                highlight.position.set(0, 4, -24);
            } else if (loc.includes("Upper Fuselage") || loc.includes("Crown")) {
                highlight.position.set(0, 3, 5);
            } else if (loc.includes("Lower Fuselage") || loc.includes("Belly")) {
                highlight.position.set(0, -3, 5);
            } else {
                // Main fuselage
                highlight.position.set(0, 0, 5);
            }
            
            // Pulsing animation data
            highlight.userData = { timeOffset: Math.random() * Math.PI };
            airplane.add(highlight);
        });

        // Handle resize
        window.addEventListener('resize', () => {
            if (!container) return;
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        });

        // Animation Loop
        const clock = new THREE.Clock();
        function animate() {
            requestAnimationFrame(animate);
            controls.update();
            
            // Pulse defect highlights
            const time = clock.getElapsedTime();
            airplane.children.forEach(child => {
                if (child.material === defectMat) {
                    const scale = 1 + Math.sin(time * 4 + child.userData.timeOffset) * 0.15;
                    child.scale.set(scale, scale, scale);
                }
            });
            
            renderer.render(scene, camera);
        }
        animate();
    }
});
