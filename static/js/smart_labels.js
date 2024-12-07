document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const previewArea = document.getElementById('previewArea');
    const previewImage = document.getElementById('previewImage');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resetBtn = document.getElementById('resetBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsArea = document.getElementById('resultsArea');
    const startCameraBtn = document.getElementById('startCamera');
    const cameraFeed = document.getElementById('cameraFeed');
    const captureBtn = document.getElementById('captureBtn');
    
    let stream = null;
    let isCameraActive = false;

    // Debug logging
    function debug(message) {
        console.log(`[Smart Labels Debug] ${message}`);
    }

    // Drag and drop handling
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('dragover');
        });
    });

    // Handle file drop
    uploadArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleImage(files[0]);
        }
    });

    // Handle file selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleImage(e.target.files[0]);
        }
    });

    // Camera handling
    async function initCamera() {
        debug('Initializing camera...');
        try {
            // Request camera with preferred settings
            const constraints = {
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                    frameRate: { ideal: 30 }
                }
            };

            stream = await navigator.mediaDevices.getUserMedia(constraints);
            debug('Camera stream obtained');

            // Set up video element
            cameraFeed.srcObject = stream;
            cameraFeed.style.display = 'block';
            captureBtn.style.display = 'inline-block';
            startCameraBtn.textContent = 'Stop Camera';
            startCameraBtn.classList.remove('btn-primary');
            startCameraBtn.classList.add('btn-danger');
            uploadArea.style.display = 'none';
            isCameraActive = true;

            // Wait for video to be ready
            await cameraFeed.play();
            debug('Camera feed active');

        } catch (err) {
            console.error('Camera error:', err);
            alert('Error accessing camera. Please ensure camera permissions are granted and try again.');
            stopCamera();
        }
    }

    function stopCamera() {
        debug('Stopping camera...');
        if (stream) {
            stream.getTracks().forEach(track => {
                track.stop();
                debug(`Stopped track: ${track.kind}`);
            });
            stream = null;
        }
        
        cameraFeed.srcObject = null;
        cameraFeed.style.display = 'none';
        captureBtn.style.display = 'none';
        startCameraBtn.textContent = 'Start Camera';
        startCameraBtn.classList.remove('btn-danger');
        startCameraBtn.classList.add('btn-primary');
        uploadArea.style.display = 'block';
        isCameraActive = false;
    }

    // Camera button click handler
    startCameraBtn.addEventListener('click', async () => {
        debug('Camera button clicked');
        if (isCameraActive) {
            stopCamera();
        } else {
            await initCamera();
        }
    });

    // Capture button click handler
    captureBtn.addEventListener('click', () => {
        debug('Capture button clicked');
        if (!cameraFeed.srcObject) {
            debug('No video stream available');
            return;
        }

        const canvas = document.createElement('canvas');
        canvas.width = cameraFeed.videoWidth;
        canvas.height = cameraFeed.videoHeight;
        
        debug(`Capturing image: ${canvas.width}x${canvas.height}`);
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(cameraFeed, 0, 0);
        
        canvas.toBlob((blob) => {
            debug('Image captured, processing...');
            handleImage(blob);
            stopCamera();
        }, 'image/jpeg', 0.95);
    });

    function handleImage(file) {
        debug('Handling image file');
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file.');
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            uploadArea.style.display = 'none';
            previewArea.style.display = 'block';
            analyzeBtn.style.display = 'inline-block';
            window.imageToAnalyze = file;
            debug('Image preview ready');
        };
        reader.readAsDataURL(file);
    }

    // Handle analysis
    analyzeBtn.addEventListener('click', async () => {
        if (!window.imageToAnalyze) {
            alert('Please select or capture an image first');
            return;
        }

        try {
            debug('Starting analysis...');
            loadingSpinner.style.display = 'block';
            previewArea.style.display = 'none';
            resultsArea.style.display = 'none';
            
            const formData = new FormData();
            formData.append('image', window.imageToAnalyze);
            
            debug('Sending image to server...');
            const response = await fetch('/analyze-product', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            debug(`Analysis response received: ${data.status}`);
            
            if (data.status === 'success') {
                displayResults(data.analysis);
            } else {
                throw new Error(data.message || 'Analysis failed');
            }
        } catch (error) {
            debug(`Analysis error: ${error.message}`);
            resultsArea.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-circle"></i>
                    ${error.message || 'An error occurred during analysis. Please try again.'}
                </div>
            `;
            resultsArea.style.display = 'block';
        } finally {
            loadingSpinner.style.display = 'none';
            previewArea.style.display = 'block';
        }
    });

    // Reset everything
    resetBtn.addEventListener('click', () => {
        debug('Resetting interface...');
        uploadArea.style.display = 'block';
        previewArea.style.display = 'none';
        resultsArea.style.display = 'none';
        loadingSpinner.style.display = 'none';
        fileInput.value = '';
        previewImage.src = '';
        window.imageToAnalyze = null;
        stopCamera();
    });

    function displayResults(analysis) {
        debug('Displaying analysis results');
        const resultsArea = document.getElementById('resultsArea');
        resultsArea.innerHTML = '';
        
        const resultContainer = document.createElement('div');
        resultContainer.className = 'result-container p-4';
        
        // Product Name
        const productName = document.createElement('h3');
        productName.className = 'mb-4 product-name';
        productName.textContent = analysis.product_name || 'Product Analysis';
        resultContainer.appendChild(productName);
        
        // Overall Assessment
        if (analysis.overall_assessment) {
            const assessment = analysis.overall_assessment;
            const assessmentDiv = document.createElement('div');
            assessmentDiv.className = 'assessment-container mb-4 p-3 border rounded';
            
            // Risk Level Badge
            const riskBadge = document.createElement('span');
            riskBadge.className = `badge ${getRiskBadgeClass(assessment.risk_level)} mb-2`;
            riskBadge.textContent = `Risk Level: ${assessment.risk_level}`;
            assessmentDiv.appendChild(riskBadge);
            
            // Competition Status
            const statusBadge = document.createElement('span');
            statusBadge.className = `badge ms-2 ${getStatusBadgeClass(assessment.competition_status)} mb-2`;
            statusBadge.textContent = `Competition: ${assessment.competition_status}`;
            assessmentDiv.appendChild(statusBadge);
            
            // Warning Message
            if (assessment.warning_message) {
                const warning = document.createElement('div');
                warning.className = 'alert alert-warning mt-2';
                warning.textContent = assessment.warning_message;
                assessmentDiv.appendChild(warning);
            }
            
            resultContainer.appendChild(assessmentDiv);
        }
        
        // Ingredients Analysis
        if (analysis.ingredients_analysis && analysis.ingredients_analysis.length > 0) {
            const ingredientsDiv = document.createElement('div');
            ingredientsDiv.className = 'ingredients-container mb-4';
            
            const ingredientsTitle = document.createElement('h4');
            ingredientsTitle.className = 'mb-3';
            ingredientsTitle.textContent = 'Ingredients Analysis';
            ingredientsDiv.appendChild(ingredientsTitle);
            
            const table = document.createElement('table');
            table.className = 'table table-striped';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Ingredient</th>
                        <th>Status</th>
                        <th>Category</th>
                        <th>Warning</th>
                    </tr>
                </thead>
                <tbody>
                    ${analysis.ingredients_analysis.map(ingredient => `
                        <tr>
                            <td>${ingredient.name}</td>
                            <td><span class="badge ${getStatusBadgeClass(ingredient.status)}">${ingredient.status}</span></td>
                            <td>${ingredient.category || '-'}</td>
                            <td>${ingredient.warning || '-'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
            ingredientsDiv.appendChild(table);
            resultContainer.appendChild(ingredientsDiv);
        }
        
        // Recommendations
        if (analysis.recommendations && analysis.recommendations.length > 0) {
            const recsDiv = document.createElement('div');
            recsDiv.className = 'recommendations-container mb-4';
            
            const recsTitle = document.createElement('h4');
            recsTitle.className = 'mb-3';
            recsTitle.textContent = 'Recommendations';
            recsDiv.appendChild(recsTitle);
            
            const recsList = document.createElement('ul');
            recsList.className = 'list-group';
            analysis.recommendations.forEach(rec => {
                const item = document.createElement('li');
                item.className = 'list-group-item';
                item.textContent = rec;
                recsList.appendChild(item);
            });
            recsDiv.appendChild(recsList);
            resultContainer.appendChild(recsDiv);
        }
        
        // Source Badge (if using fallback)
        if (analysis.source === 'fallback') {
            const sourceBadge = document.createElement('div');
            sourceBadge.className = 'alert alert-info mt-3';
            sourceBadge.innerHTML = '<i class="fas fa-info-circle"></i> Using basic analysis mode - results may be limited';
            resultContainer.appendChild(sourceBadge);
        }
        
        resultsArea.appendChild(resultContainer);
        resultsArea.style.display = 'block';
        debug('Results displayed');
    }
    
    function getRiskBadgeClass(risk) {
        switch (risk?.toUpperCase()) {
            case 'HIGH':
                return 'bg-danger';
            case 'MEDIUM':
                return 'bg-warning text-dark';
            case 'LOW':
                return 'bg-success';
            default:
                return 'bg-secondary';
        }
    }
    
    function getStatusBadgeClass(status) {
        switch (status?.toUpperCase()) {
            case 'PROHIBITED':
                return 'bg-danger';
            case 'IN-COMPETITION':
            case 'THRESHOLD':
            case 'CAUTION':
                return 'bg-warning text-dark';
            case 'SAFE':
                return 'bg-success';
            default:
                return 'bg-secondary';
        }
    }
});
