// RMRIMS Reporting System 2026 - Interactive Scripts

// ── Mobile Navigation Toggle ──
function toggleMobileNav() {
    const btn = document.getElementById('hamburgerBtn');
    const nav = document.getElementById('mobileNav');
    if (!btn || !nav) return;
    btn.classList.toggle('open');
    nav.classList.toggle('open');
}

// Close mobile nav when clicking outside
document.addEventListener('click', function(e) {
    const btn = document.getElementById('hamburgerBtn');
    const nav = document.getElementById('mobileNav');
    if (!btn || !nav) return;
    if (!btn.contains(e.target) && !nav.contains(e.target)) {
        btn.classList.remove('open');
        nav.classList.remove('open');
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Check if we are on the Report Form page
    const reportForm = document.getElementById('report-form');
    if (reportForm) {
        initReportForm();
    }
});

// Report Form Logic
function initReportForm() {
    const testSelect = document.getElementById('test-select');
    const resultInput = document.getElementById('result-input');
    const interpPreview = document.getElementById('interpretation-preview');
    const addTestBtn = document.getElementById('add-test-btn');
    const testsTableBody = document.getElementById('tests-table-body');
    const testsDataJson = document.getElementById('tests-data-json');
    
    // Internal state for tests list
    let testsList = [];
    
    // Check if we have pre-existing tests (in Edit Mode)
    const existingTestsData = document.getElementById('existing-tests-data');
    if (existingTestsData && existingTestsData.value) {
        try {
            testsList = JSON.parse(existingTestsData.value);
            renderTestsTable();
        } catch(e) {
            console.error("Error parsing existing tests data", e);
        }
    }
    
    // Result toggle based on method
    function toggleResultInput() {
        const testMethodInput = document.getElementById('test_method');
        const method = testMethodInput ? testMethodInput.value.trim().toUpperCase() : 'ELISA';
        const resultInput = document.getElementById('result-input');
        const resultSelect = document.getElementById('result-select');
        const interpPreviewContainer = document.getElementById('interpretation-preview-container');
        const autoInterpHeader = document.getElementById('th-auto-interpretation');
        
        if (method === 'RAPID') {
            if (resultInput) resultInput.style.display = 'none';
            if (resultSelect) resultSelect.style.display = 'block';
            if (interpPreviewContainer) interpPreviewContainer.style.display = 'none';
            if (autoInterpHeader) autoInterpHeader.style.display = 'none';
        } else {
            if (resultInput) resultInput.style.display = 'block';
            if (resultSelect) resultSelect.style.display = 'none';
            if (interpPreviewContainer) interpPreviewContainer.style.display = 'block';
            if (autoInterpHeader) autoInterpHeader.style.display = 'table-cell';
        }
        
        // Re-render table to hide/show column
        renderTestsTable();
    }
    
    const testMethodInput = document.getElementById('test_method');
    if (testMethodInput) {
        testMethodInput.addEventListener('input', toggleResultInput);
        testMethodInput.addEventListener('change', toggleResultInput);
        setTimeout(toggleResultInput, 100); // init
    }

    // Live calculation of interpretation
    function calculateInterpretation(value) {
        if (value === '') return '';
        
        const method = testMethodInput ? testMethodInput.value.trim().toUpperCase() : 'ELISA';
        const testName = testSelect ? testSelect.value.trim() : '';
        
        if (method === 'ELISA') {
            const val = parseFloat(value);
            if (isNaN(val)) return '';
            if (testName === 'HBsAg') {
                return val >= 0.191 ? 'Positive' : 'Negative';
            } else if (testName === 'HCV Antibody') {
                return val >= 0.361 ? 'Positive' : 'Negative';
            } else {
                if (val < 9.0) return 'Negative';
                else if (val > 11.0) return 'Positive';
                else return 'Equivocal';
            }
        } else {
            // For RT-PCR, RAPID, etc. - parse from text
            const lower = value.toLowerCase();
            if (['positive', 'negative', 'equivocal', 'invalid'].includes(lower)) {
                return value.charAt(0).toUpperCase() + lower.slice(1);
            }
            return '';
        }
    }
    
    function updateLivePreview() {
        const value = resultInput.value;
        const interpretation = calculateInterpretation(value);
        
        if (interpretation) {
            interpPreview.textContent = `Interpretation: ${interpretation}`;
            interpPreview.className = `interpretation-preview-text ${interpretation.toLowerCase()}`;
        } else {
            interpPreview.textContent = '';
            interpPreview.className = 'interpretation-preview-text';
        }
    }
    
    // Update live preview when result input changes
    resultInput.addEventListener('input', updateLivePreview);
    if (testSelect) {
        testSelect.addEventListener('input', updateLivePreview);
        testSelect.addEventListener('change', updateLivePreview);
    }
    
    // Add Test Button Handler
    addTestBtn.addEventListener('click', function() {
        const method = testMethodInput ? testMethodInput.value.trim().toUpperCase() : 'ELISA';
        const testName = testSelect.value;
        let resultVal = '';
        
        if (method === 'RAPID') {
            const resultSelect = document.getElementById('result-select');
            resultVal = resultSelect ? resultSelect.value : '';
        } else {
            resultVal = resultInput.value.trim();
        }
        
        if (!testName) {
            alert('Please select a test name.');
            return;
        }
        if (resultVal === '') {
            alert('Please enter a valid result value.');
            return;
        }
        
        // Check if test already exists in list
        const exists = testsList.some(item => item.test_name === testName);
        if (exists) {
            if (!confirm(`"${testName}" is already added. Do you want to overwrite its value?`)) {
                return;
            }
            // Overwrite
            testsList = testsList.filter(item => item.test_name !== testName);
        }
        
        // Add to list
        testsList.push({
            test_name: testName,
            result_value: resultVal,
            interpretation: calculateInterpretation(resultVal)
        });
        
        // Clear input
        resultInput.value = '';
        interpPreview.textContent = '';
        
        // Re-render and update hidden field
        renderTestsTable();
        updateHiddenJson();
    });
    
    // Render tests table
    function renderTestsTable() {
        testsTableBody.innerHTML = '';
        
        if (testsList.length === 0) {
            testsTableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center" style="color: var(--text-muted); font-style: italic;">
                        No tests added yet. Select a test and enter a result value above.
                    </td>
                </tr>
            `;
            return;
        }
        
        const method = testMethodInput ? testMethodInput.value.trim().toUpperCase() : 'ELISA';

        testsList.forEach((item, index) => {
            const tr = document.createElement('tr');
            
            let badgeClass = 'badge-equivocal';
            if (item.interpretation === 'Negative') badgeClass = 'badge-negative';
            if (item.interpretation === 'Positive') badgeClass = 'badge-positive';
            
            let interpTd = `<td><span class="badge ${badgeClass}">${item.interpretation}</span></td>`;
            if (method === 'RAPID') {
                interpTd = `<td style="display:none;"></td>`;
            }
            
            tr.innerHTML = `
                <td><strong>${item.test_name}</strong></td>
                ${interpTd}
                <td><strong>${item.result_value}</strong></td>
                <td>
                    <button type="button" class="btn-icon delete remove-test-btn" data-index="${index}" title="Remove Test">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
                    </button>
                </td>
            `;
            testsTableBody.appendChild(tr);
        });
        
        // Attach click handlers to remove buttons
        const removeButtons = testsTableBody.querySelectorAll('.remove-test-btn');
        removeButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const idx = parseInt(this.getAttribute('data-index'));
                testsList.splice(idx, 1);
                renderTestsTable();
                updateHiddenJson();
            });
        });
    }
    
    // Update Hidden Input field before form submission
    function updateHiddenJson() {
        testsDataJson.value = JSON.stringify(testsList);
    }
    
    // Final validation before submit
    const reportFormElement = document.getElementById('report-form');
    reportFormElement.addEventListener('submit', function(e) {
        updateHiddenJson();
        if (testsList.length === 0) {
            e.preventDefault();
            alert('Please add at least one test to the report before saving.');
        }
    });
}
