// Simplified Global state
let selectedModels = [];

// Enhanced model options for Wall Street quality
const modelOptions = [
    {
        id: 'dcf',
        title: 'DCF Model',
        icon: 'fas fa-chart-line',
        description: 'Discounted Cash Flow valuation with institutional-grade analysis',
        features: ['5-year projections', 'Terminal value calculation', 'WACC analysis', 'Sensitivity tables']
    },
    {
        id: 'lbo',
        title: 'LBO Model', 
        icon: 'fas fa-handshake',
        description: 'Leveraged Buyout analysis with private equity standard returns',
        features: ['Sources & Uses', 'Debt scheduling', 'IRR & MOIC', 'Exit scenarios']
    },
    {
        id: 'comps',
        title: 'Comparable Analysis',
        icon: 'fas fa-balance-scale',
        description: 'Trading multiples and peer comparison analysis',
        features: ['Trading multiples', 'Peer analysis', 'Valuation ranges', 'Market positioning']
    },
    {
        id: '3-statement',
        title: '3-Statement Model',
        icon: 'fas fa-table',
        description: 'Integrated financial statements with dynamic linking',
        features: ['Income Statement', 'Balance Sheet', 'Cash Flow', 'Dynamic linking']
    },
    {
        id: 'ma',
        title: 'M&A Analysis',
        icon: 'fas fa-handshake',
        description: 'Merger & Acquisition accretion/dilution analysis',
        features: ['Accretion/Dilution', 'Synergies analysis', 'Pro forma statements', 'Deal metrics']
    },
    {
        id: 'ipo',
        title: 'IPO Model',
        icon: 'fas fa-rocket',
        description: 'Initial Public Offering valuation and pricing model',
        features: ['Valuation range', 'Use of proceeds', 'Comparables', 'Market conditions']
    },
    {
        id: 'options',
        title: 'Options Pricing',
        icon: 'fas fa-calculator',
        description: 'Black-Scholes options valuation with Greeks',
        features: ['Black-Scholes model', 'Greeks calculation', 'Volatility analysis', 'Strike scenarios']
    }
];

document.addEventListener('DOMContentLoaded', function() {
    populateModels();
    setupEventListeners();
});

function setupEventListeners() {
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', handleGenerate);
    }

    const generateMoreBtn = document.getElementById('generateMoreBtn');
    if (generateMoreBtn) {
        generateMoreBtn.addEventListener('click', resetToInput);
    }
}

function populateModels() {
    const modelsContainer = document.getElementById('modelsGrid');
    if (!modelsContainer) return;
    
    modelsContainer.innerHTML = '';
    
    modelOptions.forEach(model => {
        const modelCard = createModelCard(model);
        modelsContainer.appendChild(modelCard);
    });
}

function createModelCard(model) {
    const card = document.createElement('div');
    card.className = 'model-card';
    card.dataset.modelId = model.id;
    
    card.innerHTML = `
        <div class="model-header">
            <i class="${model.icon}"></i>
            <div class="model-title">${model.title}</div>
            <div class="included-badge">Included</div>
        </div>
        <div class="model-description">${model.description}</div>
        <div class="model-features">
            ${model.features.map(feature => `<span class="feature-tag">${feature}</span>`).join('')}
        </div>
    `;
    
    card.addEventListener('click', () => toggleModel(model.id, card));
    
    return card;
}

function toggleModel(modelId, cardElement) {
    const index = selectedModels.indexOf(modelId);
    
    if (index > -1) {
        selectedModels.splice(index, 1);
        cardElement.classList.remove('selected');
    } else {
        selectedModels.push(modelId);
        cardElement.classList.add('selected');
    }
    
    updateModelSelections();
}

function updateModelSelections() {
    const generateBtn = document.getElementById('generateBtn');
    const count = selectedModels.length;
    
    if (count === 0) {
        generateBtn.innerHTML = '<i class="fas fa-download"></i> Select Models to Generate';
        generateBtn.disabled = true;
    } else {
        generateBtn.innerHTML = `<i class="fas fa-download"></i> Generate ${count} Professional Excel Model${count > 1 ? 's' : ''}`;
        generateBtn.disabled = false;
    }
}

function handleGenerate() {
    // Enhanced input validation
    const companyName = document.getElementById('companyName').value.trim();
    const tickerSymbol = document.getElementById('tickerSymbol').value.trim().toUpperCase();
    
    if (!companyName) {
        showError('Missing Information', 'Please enter a company name.');
        return;
    }
    
    if (!tickerSymbol) {
        showError('Missing Information', 'Please enter a ticker symbol.');
        return;
    }
    
    if (selectedModels.length === 0) {
        showError('No Models Selected', 'Please select at least one financial model to generate.');
        return;
    }

    // Show loading screen
    showLoading();
    
    // Make API request for Excel generation
    fetch('/api/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            company_name: companyName,
            ticker: tickerSymbol,
            models: selectedModels
        })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => Promise.reject(err));
        }
        return response.json();
    })
    .then(data => {
        hideLoading();
        
        if (data.success && data.results && data.results.length > 0) {
            showResults(data);
        } else {
            showError('Generation Failed', 
                data.error || 'Failed to generate financial models. Please try again.');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Generation error:', error);
        showError('Generation Error', 
            error.error || error.message || 'An unexpected error occurred. Please try again.');
    });
}

function showLoading() {
    document.getElementById('companySection').classList.add('hidden');
    document.getElementById('modelSection').classList.add('hidden');
    document.getElementById('loadingScreen').classList.remove('hidden');
    
    // Enhanced loading steps for Excel generation
    const steps = [
        'Fetching real financial data from Yahoo Finance...',
        'Analyzing company fundamentals and ratios...',
        'Building Wall Street-grade financial models...',
        'Applying professional Excel formatting...',
        'Creating industry-specific assumptions...',
        'Generating sensitivity analysis tables...',
        'Finalizing your professional Excel files...'
    ];
    
    animateLoadingSteps(steps);
}

function animateLoadingSteps(steps) {
    const stepsList = document.querySelector('.loading-steps');
    stepsList.innerHTML = '';
    
    steps.forEach((step, index) => {
        const stepElement = document.createElement('div');
        stepElement.className = 'loading-step';
        stepElement.innerHTML = `
            <div class="step-icon">
                <i class="fas fa-circle-notch fa-spin"></i>
            </div>
            <div class="step-text">${step}</div>
        `;
        stepsList.appendChild(stepElement);
        
        // Animate each step with delay
        setTimeout(() => {
            stepElement.classList.add('active');
            
            // Mark as complete after some time
            setTimeout(() => {
                stepElement.classList.add('complete');
                stepElement.querySelector('.step-icon').innerHTML = 
                    '<i class="fas fa-check-circle"></i>';
            }, 2000 + (index * 500));
            
        }, index * 800);
    });
}

function hideLoading() {
    document.getElementById('loadingScreen').classList.add('hidden');
}

function showResults(data) {
    // Enhanced results display for Excel files
    const resultsSection = document.getElementById('resultsSection');
    const resultsGrid = document.getElementById('resultsGrid');
    
    resultsGrid.innerHTML = '';
    
    // Add summary information
    const summaryCard = document.createElement('div');
    summaryCard.className = 'result-summary';
    summaryCard.innerHTML = `
        <h3>📊 Wall Street Models Generated</h3>
        <div class="summary-stats">
            <div class="stat">
                <span class="stat-number">${data.summary.successfully_created}</span>
                <span class="stat-label">Excel Models Created</span>
            </div>
            <div class="stat">
                <span class="stat-number">${data.data_quality === 'fetched' ? '✅' : '⚠️'}</span>
                <span class="stat-label">Data Quality: ${data.data_quality.charAt(0).toUpperCase() + data.data_quality.slice(1)}</span>
            </div>
        </div>
        ${data.warnings && data.warnings.length > 0 ? 
            `<div class="data-warnings">
                <h4>⚠️ Data Quality Notes:</h4>
                <ul>${data.warnings.map(w => `<li>${w}</li>`).join('')}</ul>
            </div>` : ''}
        ${data.manual_inputs_needed && data.manual_inputs_needed.length > 0 ? 
            `<div class="manual-inputs">
                <h4>📝 Manual Review Recommended:</h4>
                <p>Please review these assumptions in your Excel files: ${data.manual_inputs_needed.join(', ')}</p>
            </div>` : ''}
    `;
    resultsGrid.appendChild(summaryCard);
    
    // Add individual model results
    data.results.forEach(result => {
        const resultCard = createResultCard(result);
        resultsGrid.appendChild(resultCard);
    });
    
    resultsSection.classList.remove('hidden');
}

function createResultCard(fileData) {
    const card = document.createElement('div');
    card.className = 'result-card';
    
    const modelOption = modelOptions.find(m => m.id === fileData.model_type.toLowerCase());
    
    card.innerHTML = `
        <div class="result-header">
            <i class="${modelOption ? modelOption.icon : 'fas fa-file-excel'}"></i>
            <div class="result-title">${fileData.model_type} Model</div>
            <div class="success-badge">✅ Ready</div>
        </div>
        <div class="result-company">${fileData.company} - Professional Excel Model</div>
        <div class="result-actions">
            <a href="${fileData.download_url}" class="download-link" download>
                <i class="fas fa-download"></i>
                Download Excel File
            </a>
        </div>
        ${fileData.warnings && fileData.warnings.length > 0 ? 
            `<div class="sheet-warnings">
                <small>⚠️ Contains estimated data - review highlighted cells</small>
            </div>` : ''}
    `;
    
    return card;
}

function resetToInput() {
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('companySection').classList.remove('hidden');
    document.getElementById('modelSection').classList.remove('hidden');
    
    // Clear previous selections
    selectedModels = [];
    document.querySelectorAll('.model-card.selected').forEach(card => {
        card.classList.remove('selected');
    });
    updateModelSelections();
    
    // Clear form data
    document.getElementById('companyName').value = '';
    document.getElementById('tickerSymbol').value = '';
}

function showError(title, message) {
    // Enhanced error modal
    const errorModal = document.createElement('div');
    errorModal.className = 'error-modal';
    errorModal.innerHTML = `
        <div class="error-content">
            <div class="error-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h3>${title}</h3>
            <p>${message}</p>
            <button onclick="this.closest('.error-modal').remove()" class="error-close-btn">
                Got it
            </button>
        </div>
    `;
    
    document.body.appendChild(errorModal);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (errorModal.parentNode) {
            errorModal.remove();
        }
    }, 10000);
}

function showInfo() {
    // Info modal explaining how it works
    const infoModal = document.createElement('div');
    infoModal.className = 'info-modal';
    infoModal.innerHTML = `
        <div class="info-content">
            <div class="info-icon">
                <i class="fas fa-info-circle"></i>
            </div>
            <h3>How It Works</h3>
            <div class="info-steps">
                <div class="info-step">
                    <i class="fas fa-building"></i>
                    <div>
                        <h4>1. Enter Company</h4>
                        <p>Input any public company name and ticker symbol</p>
                    </div>
                </div>
                <div class="info-step">
                    <i class="fas fa-mouse-pointer"></i>
                    <div>
                        <h4>2. Select Models</h4>
                        <p>Choose from 7 professional Wall Street financial models</p>
                    </div>
                </div>
                <div class="info-step">
                    <i class="fas fa-download"></i>
                    <div>
                        <h4>3. Download Excel</h4>
                        <p>Get perfectly formatted, investment-grade Excel files</p>
                    </div>
                </div>
            </div>
            <div class="info-features">
                <h4>What You Get:</h4>
                <ul>
                    <li>✅ Real financial data from Yahoo Finance</li>
                    <li>✅ Professional Wall Street formatting</li>
                    <li>✅ Industry-specific assumptions</li>
                    <li>✅ Sensitivity analysis tables</li>
                    <li>✅ Investment-banking quality</li>
                </ul>
            </div>
            <button onclick="this.closest('.info-modal').remove()" class="info-close-btn">
                Start Creating Models
            </button>
        </div>
    `;
    
    document.body.appendChild(infoModal);
} 