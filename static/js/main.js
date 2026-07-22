// RMRIMS Reporting System 2026 - Interactive Scripts

// ── Mobile Navigation Toggle ──
function toggleMobileNav() {
    const btn = document.getElementById('hamburgerBtn');
    const nav = document.getElementById('mobileNav');
    if (!btn || !nav) return;
    btn.classList.toggle('open');
    nav.classList.toggle('open');
}

document.addEventListener('click', function (e) {
    const btn = document.getElementById('hamburgerBtn');
    const nav = document.getElementById('mobileNav');
    if (!btn || !nav) return;
    if (!btn.contains(e.target) && !nav.contains(e.target)) {
        btn.classList.remove('open');
        nav.classList.remove('open');
    }
});

document.addEventListener('DOMContentLoaded', function () {
    // Check if we are on the Report Form page
    const reportForm = document.getElementById('report-form');
    if (reportForm) {
        initReportForm();
    }
});// Report Form Logic
function initReportForm() {
    const testSelect = document.getElementById('test-select');
    const resultInput = document.getElementById('result-input');
    const interpPreview = document.getElementById('interpretation-preview');
    const addTestBtn = document.getElementById('add-test-btn');
    const testsTableBody = document.getElementById('tests-table-body');
    const testsDataJson = document.getElementById('tests-data-json');
    const testCategorySelect = document.getElementById('test-category-select');

    // UI input containers
    const resultInputGroup = document.getElementById('result-input-group');
    const resultInputLabel = document.getElementById('result-input-label');
    const statusSelectGroup = document.getElementById('status-select-group');
    const statusSelect = document.getElementById('status-select');
    const interpPreviewContainer = document.getElementById('interpretation-preview-container');

    // Internal state for tests list
    let testsList = [];

    // Parse test configuration from embedded json element if present
    let testConfigs = {};
    const configsScript = document.getElementById('test-configs-data');
    if (configsScript && configsScript.textContent) {
        try {
            testConfigs = JSON.parse(configsScript.textContent);
        } catch (e) {
            console.error("Error parsing test configurations from DOM", e);
        }
    }

    // Check if we have pre-existing tests (in Edit Mode)
    const existingTestsData = document.getElementById('existing-tests-data');
    if (existingTestsData && existingTestsData.value) {
        try {
            testsList = JSON.parse(existingTestsData.value);
            testsList = testsList.map(item => {
                let cat = item.test_method || 'ELISA';
                let interp = item.interpretation;
                if (!interp) {
                    interp = calculateInterpretation(item.result_value, item.test_name, cat);
                }
                return {
                    test_name: item.test_name,
                    result_value: item.result_value,
                    interpretation: interp,
                    test_method: cat
                };
            });
            renderTestsTable();
        } catch (e) {
            console.error("Error parsing existing tests data", e);
        }
    }

    // Result toggle based on method & config
    function updateInputsForSelectedTest() {
        const method = testCategorySelect ? testCategorySelect.value.trim().toUpperCase() : 'ELISA';
        const name = testSelect ? testSelect.value.trim() : '';

        // Find if there is a custom configuration for this method + test name
        let config = null;
        if (testConfigs[method] && testConfigs[method][name]) {
            config = testConfigs[method][name];
        }

        if (config) {
            const rt = config.result_type;
            if (rt === 'positive_negative' || rt === 'select' || rt === 'reactive_non_reactive' || rt === 'custom_dropdown') {
                // Show dropdown, hide text input, hide live preview
                if (resultInputGroup) resultInputGroup.style.display = 'none';
                if (statusSelectGroup) {
                    statusSelectGroup.style.display = 'block';
                    // Re-render dropdown options
                    statusSelect.innerHTML = '<option value="">-- Select Status --</option>';

                    let opts = [];
                    if (rt === 'positive_negative') {
                        opts = ['Positive', 'Negative'];
                    } else if (rt === 'select') {
                        opts = ['Positive', 'Negative', 'Equivocal'];
                    } else if (rt === 'reactive_non_reactive') {
                        opts = ['Reactive', 'Non-Reactive'];
                    } else if (rt === 'custom_dropdown' && config.custom_options) {
                        opts = config.custom_options.split(',').map(o => o.trim()).filter(o => o);
                    }

                    opts.forEach(opt => {
                        statusSelect.innerHTML += `<option value="${opt}">${opt}</option>`;
                    });
                }
                if (interpPreviewContainer) interpPreviewContainer.style.display = 'none';
            } else {
                // Numeric
                if (resultInputGroup) {
                    resultInputGroup.style.display = 'block';
                    if (resultInputLabel) resultInputLabel.textContent = 'Result Value';
                    if (resultInput) resultInput.placeholder = 'e.g. 2.959';
                }
                if (statusSelectGroup) statusSelectGroup.style.display = 'none';
                if (interpPreviewContainer) interpPreviewContainer.style.display = 'block';
            }
        } else {
            // No custom config: fall back to default behavior
            if (method === 'RAPID') {
                if (resultInputGroup) resultInputGroup.style.display = 'none';
                if (statusSelectGroup) {
                    statusSelectGroup.style.display = 'block';
                    statusSelect.innerHTML = `
                        <option value="">-- Select Status --</option>
                        <option value="Positive">Positive</option>
                        <option value="Negative">Negative</option>
                    `;
                }
                if (interpPreviewContainer) interpPreviewContainer.style.display = 'none';
            } else if (method === 'RT-PCR') {
                if (resultInputGroup) {
                    resultInputGroup.style.display = 'block';
                    if (resultInputLabel) resultInputLabel.textContent = 'Result Value (Optional)';
                    if (resultInput) resultInput.placeholder = 'e.g. 24.5 (Optional)';
                }
                if (statusSelectGroup) {
                    statusSelectGroup.style.display = 'block';
                    statusSelect.innerHTML = `
                        <option value="">-- Select Status --</option>
                        <option value="Positive">Positive</option>
                        <option value="Negative">Negative</option>
                    `;
                }
                if (interpPreviewContainer) interpPreviewContainer.style.display = 'none';
            } else {
                // ELISA default
                if (resultInputGroup) {
                    resultInputGroup.style.display = 'block';
                    if (resultInputLabel) resultInputLabel.textContent = 'Result Value';
                    if (resultInput) resultInput.placeholder = 'e.g. 2.959';
                }
                if (statusSelectGroup) statusSelectGroup.style.display = 'none';
                if (interpPreviewContainer) interpPreviewContainer.style.display = 'block';
            }
        }
        updateLivePreview();
    }

    if (testCategorySelect) {
        testCategorySelect.addEventListener('input', updateInputsForSelectedTest);
        testCategorySelect.addEventListener('change', updateInputsForSelectedTest);
        setTimeout(updateInputsForSelectedTest, 100); // init
    }
    if (testSelect) {
        testSelect.addEventListener('input', updateInputsForSelectedTest);
        testSelect.addEventListener('change', updateInputsForSelectedTest);
    }

    // Live calculation of interpretation
    function calculateInterpretation(value, testName, category) {
        if (value === '') return '';

        const method = category || (testCategorySelect ? testCategorySelect.value.trim().toUpperCase() : 'ELISA');
        const name = testName || (testSelect ? testSelect.value.trim() : '');

        // Check if there is a custom test configuration first
        if (testConfigs[method] && testConfigs[method][name]) {
            const config = testConfigs[method][name];
            const rt = config.result_type;
            if (rt === 'positive_negative' || rt === 'select' || rt === 'reactive_non_reactive' || rt === 'custom_dropdown') {
                return ''; // Dropdown option will supply interpretation directly
            }

            // Numeric configuration interpretation
            const val = parseFloat(value);
            if (isNaN(val)) return '';

            const lower = config.cutoff_value;
            const upper = config.cutoff_value_upper;

            if (lower !== null && lower !== undefined) {
                if (upper !== null && upper !== undefined) {
                    if (val < lower) return 'Negative';
                    else if (val >= upper) return 'Positive';
                    else return 'Equivocal';
                } else {
                    return val >= lower ? 'Positive' : 'Negative';
                }
            }
        }

        if (method.toUpperCase() === 'ELISA') {
            const val = parseFloat(value);
            if (isNaN(val)) return '';
            if (name === 'HBsAg') {
                return val >= 0.191 ? 'Reactive' : 'Non-Reactive';
            } else if (name === 'HCV Antibody') {
                return val >= 0.361 ? 'Reactive' : 'Non-Reactive';
            } else {
                if (val < 9.0) return 'Negative';
                else if (val > 11.0) return 'Positive';
                else return 'Equivocal';
            }
        }
        return '';
    }

    function updateLivePreview() {
        const value = resultInput.value;
        const testName = testSelect ? testSelect.value.trim() : '';
        const interpretation = calculateInterpretation(value, testName);

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

    // Add Test Button Handler
    addTestBtn.addEventListener('click', function () {
        const method = testCategorySelect ? testCategorySelect.value.trim().toUpperCase() : 'ELISA';
        const testName = testSelect.value.trim();
        let resultVal = '';
        let statusVal = '';

        // Find if there is a custom configuration
        let config = null;
        if (testConfigs[method] && testConfigs[method][testName]) {
            config = testConfigs[method][testName];
        }

        const isDropdownType = config && (config.result_type === 'positive_negative' || config.result_type === 'select' || config.result_type === 'reactive_non_reactive' || config.result_type === 'custom_dropdown');

        if (isDropdownType || method === 'RAPID') {
            statusVal = statusSelect ? statusSelect.value : '';
            resultVal = statusVal;
        } else if (method === 'RT-PCR') {
            resultVal = resultInput.value.trim() || '-';
            statusVal = statusSelect ? statusSelect.value : '';
        } else {
            // ELISA or custom numeric
            resultVal = resultInput.value.trim();
            statusVal = calculateInterpretation(resultVal, testName, method);
        }

        if (!testName) {
            alert('Please select or type a test name.');
            return;
        }

        if (isDropdownType || method === 'RAPID' || method === 'RT-PCR') {
            if (statusVal === '') {
                alert('Please select a result status.');
                return;
            }
        } else {
            if (resultVal === '') {
                alert('Please enter a valid result value.');
                return;
            }
            if (isNaN(parseFloat(resultVal))) {
                alert('Please enter a numeric result value.');
                return;
            }
        }

        // Check if test already exists in list for this method
        const exists = testsList.some(item => item.test_name === testName && (item.test_method || 'ELISA') === method);
        if (exists) {
            if (!confirm(`"${testName}" is already added under category ${method}. Do you want to overwrite its value?`)) {
                return;
            }
            testsList = testsList.filter(item => !(item.test_name === testName && (item.test_method || 'ELISA') === method));
        }

        // Add to list
        testsList.push({
            test_name: testName,
            result_value: resultVal,
            interpretation: statusVal,
            test_method: testCategorySelect ? testCategorySelect.value : 'ELISA'
        });

        // Clear input
        resultInput.value = '';
        if (statusSelect) statusSelect.value = '';
        interpPreview.textContent = '';

        renderTestsTable();
        updateHiddenJson();
    });

    // Render tests table
    function renderTestsTable() {
        testsTableBody.innerHTML = '';

        if (testsList.length === 0) {
            testsTableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center" style="color: var(--text-muted); font-style: italic;">
                        No tests added yet. Select a category, test name and enter the result above.
                    </td>
                </tr>
            `;
            return;
        }

        testsList.forEach((item, index) => {
            const tr = document.createElement('tr');

            let badgeClass = 'badge-equivocal';
            const interpLower = (item.interpretation || '').toLowerCase();
            if (interpLower === 'negative' || interpLower === 'non-reactive') badgeClass = 'badge-negative';
            else if (interpLower === 'positive' || interpLower === 'reactive') badgeClass = 'badge-positive';

            tr.innerHTML = `
                <td><strong>${item.test_name}</strong></td>
                <td><span class="badge" style="background-color: var(--secondary); color: white;">${item.test_method || 'ELISA'}</span></td>
                <td><strong>${item.result_value || '-'}</strong></td>
                <td><span class="badge ${badgeClass}">${item.interpretation || '-'}</span></td>
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
            btn.addEventListener('click', function () {
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
    if (reportFormElement) {
        reportFormElement.addEventListener('submit', function (e) {
            updateHiddenJson();
            if (testsList.length === 0) {
                e.preventDefault();
                alert('Please add at least one test to the report before saving.');
            }
        });
    }
}
