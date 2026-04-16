document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('resume');
    const fileText = document.querySelector('.file-text');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');
    const errorMessage = document.getElementById('error-message');
    const resultsSection = document.getElementById('results-section');
    const valueContainer = document.querySelector('.value-container');
    const circularProgress = document.querySelector('.circular-progress');
    const suggestionsGrid = document.getElementById('suggestions-grid');
    const scannerOverlay = document.getElementById('scanner-overlay');
    const scannerText = document.getElementById('scanner-text');
    // Update file name on selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileText.textContent = e.target.files[0].name;
            errorMessage.classList.add('error-hidden');
        } else {
            fileText.textContent = 'Click to browse your PDF';
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Reset state
        errorMessage.classList.add('error-hidden');
        resultsSection.classList.add('results-hidden');
        
        const file = fileInput.files[0];
        if (!file || file.type !== 'application/pdf') {
            showError('Please select a valid PDF file.');
            return;
        }

        // Show loader
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        submitBtn.disabled = true;

        const formData = new FormData(form);

        try {
            const formData = new FormData(form);
            btnText.classList.add('hidden');
            loader.classList.remove('hidden');
            submitBtn.disabled = true;
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Something went wrong during local processing.');
            }

            // Enter Scanning Phase
            form.style.display = 'none'; // hide form temporarily
            scannerOverlay.classList.remove('scanner-hidden');
            
            const phases = [
                "Extracting semantics...",
                "Analyzing formatting & layout...",
                "Evaluating ATS keywords...",
                "Computing final impact score..."
            ];
            
            let phaseIndex = 0;
            const scannerInterval = setInterval(() => {
                scannerText.textContent = phases[phaseIndex];
                phaseIndex = (phaseIndex + 1) % phases.length;
            }, 800);
            
            setTimeout(() => {
                clearInterval(scannerInterval);
                scannerOverlay.classList.add('scanner-hidden');
                form.style.display = 'block'; // bring back form
                
                // Hide loader
                btnText.classList.remove('hidden');
                loader.classList.add('hidden');
                submitBtn.disabled = false;
                
                displayResults(data.score, data.suggestions);
            }, 3500);

        } catch (error) {
            showError(error.message);
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
            submitBtn.disabled = false;
        }
    });

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.remove('error-hidden');
    }

    function displayResults(score, suggestions) {
        resultsSection.classList.remove('results-hidden');
        
        // Render Score Animation
        let progressValue = 0;
        let progressEndValue = score;
        let speed = 20; // ms

        if(window.progressInterval) clearInterval(window.progressInterval);

        if (progressEndValue === 0) {
            valueContainer.textContent = "0";
            circularProgress.style.background = `conic-gradient(rgba(255, 255, 255, 0.1) 360deg)`;
        } else {
            window.progressInterval = setInterval(() => {
                progressValue++;
                valueContainer.textContent = progressValue;
                
                let color = '#ef4444'; // Red
                if (progressValue > 40) color = '#f59e0b'; // Yellow
                if (progressValue > 75) color = '#10b981'; // Green
                
                circularProgress.style.background = `conic-gradient(
                    ${color} ${progressValue * 3.6}deg,
                    rgba(255, 255, 255, 0.1) ${progressValue * 3.6}deg
                )`;

                if (progressValue >= progressEndValue) {
                    clearInterval(window.progressInterval);
                }
            }, speed);
        }

        // Map Suggestions into Cards
        suggestionsGrid.innerHTML = '';
        
        if (suggestions && suggestions.length > 0) {
            // Group by category
            const grouped = {};
            suggestions.forEach(sug => {
                const cat = typeof sug === 'object' ? sug.category : 'General';
                if (!grouped[cat]) grouped[cat] = [];
                grouped[cat].push(sug);
            });
            // Define the specific order for the sections
            const categoryOrder = ['Overall', 'Structure', 'Impact', 'Brevity', 'Job Match', 'General'];
            
            // Render in sequential order
            categoryOrder.forEach(category => {
                if (grouped[category]) {
                    const card = document.createElement('div');
                    card.className = 'category-card';
                    
                    const header = document.createElement('h3');
                    header.textContent = category;
                    card.appendChild(header);
                    
                    const ul = document.createElement('ul');
                    grouped[category].forEach(suggestion => {
                        const li = document.createElement('li');
                        
                        if (typeof suggestion === 'object' && suggestion !== null) {
                            const badge = document.createElement('span');
                            badge.className = `category-badge badge-${suggestion.type}`;
                            badge.textContent = suggestion.type.toUpperCase();
                            
                            const textNode = document.createTextNode(' ' + suggestion.text);
                            li.appendChild(badge);
                            li.appendChild(textNode);
                            
                            li.style.borderLeftColor = `var(--${suggestion.type})`;
                        } else {
                            li.textContent = suggestion;
                            li.style.borderLeftColor = 'var(--warning)';
                        }
                        ul.appendChild(li);
                    });
                    
                    card.appendChild(ul);
                    suggestionsGrid.appendChild(card);
                }
            });
        } else {
            suggestionsGrid.innerHTML = '<div class="category-card"><h3>✅ Perfect</h3><p>No suggestions found.</p></div>';
        }
        
        // Scroll to results smoothly
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    }
});
