/**
 * UI Management for Beam-Column Simulator
 * Handles DOM updates, event binding, and visualization
 */

class UI {
    constructor() {
        this.charts = {};
        this.bindControls();
        this.setupTabs();
    }

    /**
     * Bind input controls to state updates
     */
    bindControls() {
        // Range sliders
        ['length', 'width', 'height', 'axial-load', 'lateral-load'].forEach(id => {
            const element = document.getElementById(id);
            if (!element) return;

            element.addEventListener('input', (e) => {
                // Update display
                const displayEl = document.getElementById(`${id}-display`);
                if (displayEl) {
                    displayEl.textContent = parseFloat(e.target.value).toFixed(2);
                }

                // Update state
                const key = id.replace(/-/g, '_');
                appState.updateParameter(key, parseFloat(e.target.value));
            });
        });

        // Dropdowns
        ['material', 'end-condition'].forEach(id => {
            const element = document.getElementById(id);
            if (!element) return;

            element.addEventListener('change', (e) => {
                const key = id.replace(/-/g, '_');
                appState.updateParameter(key, e.target.value);
            });
        });

        // Radio buttons
        document.querySelectorAll('input[name="orientation"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                appState.updateParameter('orientation', e.target.value);
                this.updatePointLoadDirections();
            });
        });

        // Checkbox
        const selfWeightEl = document.getElementById('self-weight');
        if (selfWeightEl) {
            selfWeightEl.addEventListener('change', (e) => {
                appState.updateParameter('include_self_weight', e.target.checked);
            });
        }

        // Point loads number input
        const numLoadsEl = document.getElementById('num-point-loads');
        if (numLoadsEl) {
            numLoadsEl.addEventListener('change', (e) => {
                appState.setNumPointLoads(parseInt(e.target.value));
                this.renderPointLoads();
            });
        }

        // Solve button
        const solveBtn = document.getElementById('solve-btn');
        if (solveBtn) {
            solveBtn.addEventListener('click', () => this.onSolveClick());
        }

        // Export button
        const exportBtn = document.getElementById('export-csv-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportToCSV());
        }
    }

    /**
     * Render point load inputs
     */
    renderPointLoads() {
        const container = document.getElementById('point-loads-container');
        if (!container) return;

        container.innerHTML = '';

        appState.parameters.point_loads.forEach((load, index) => {
            const div = document.createElement('div');
            div.className = 'point-load-item';

            const directionOptions = appState.parameters.orientation === 'horizontal'
                ? ['downward', 'upward']
                : ['downward', 'upward'];

            const directionLabels = appState.parameters.orientation === 'horizontal'
                ? ['Down ⬇️', 'Up ⬆️']
                : ['Right →', 'Left ←'];

            div.innerHTML = `
                <div class="point-load-header">Point Load ${index + 1}</div>
                <div class="control-group">
                    <label for="pl-mag-${index}">Magnitude (kN)</label>
                    <input type="number" id="pl-mag-${index}" min="0" max="100" step="0.5"
                           value="${load.magnitude}">
                </div>
                <div class="control-group">
                    <label for="pl-pos-${index}">Position (fraction, 0-1)</label>
                    <input type="number" id="pl-pos-${index}" min="0" max="1" step="0.05"
                           value="${load.position.toFixed(2)}">
                </div>
                <div class="control-group">
                    <label>Direction</label>
                    <div class="radio-group">
                        ${directionLabels.map((label, i) => `
                            <label>
                                <input type="radio" name="pl-dir-${index}" value="${directionOptions[i]}"
                                       ${load.direction === directionOptions[i] ? 'checked' : ''}>
                                ${label}
                            </label>
                        `).join('')}
                    </div>
                </div>
            `;

            container.appendChild(div);

            // Bind events for this load
            const magEl = document.getElementById(`pl-mag-${index}`);
            magEl.addEventListener('change', (e) => {
                appState.updatePointLoad(index, { magnitude: parseFloat(e.target.value) });
            });

            const posEl = document.getElementById(`pl-pos-${index}`);
            posEl.addEventListener('change', (e) => {
                appState.updatePointLoad(index, { position: parseFloat(e.target.value) });
            });

            document.querySelectorAll(`input[name="pl-dir-${index}"]`).forEach(radio => {
                radio.addEventListener('change', (e) => {
                    appState.updatePointLoad(index, { direction: e.target.value });
                });
            });
        });
    }

    /**
     * Update point load directions when orientation changes
     */
    updatePointLoadDirections() {
        this.renderPointLoads();
    }

    /**
     * Setup tab switching
     */
    setupTabs() {
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    /**
     * Switch to a different tab
     */
    switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });

        // Deactivate all buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected tab
        const tabEl = document.getElementById(`${tabName}-tab`);
        if (tabEl) {
            tabEl.classList.add('active');
        }

        // Activate button
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Trigger chart resize on charts tab
        if (tabName === 'charts') {
            setTimeout(() => {
                Object.values(this.charts).forEach(chart => {
                    if (chart && chart.resize) {
                        chart.resize();
                    }
                });
            }, 0);
        }
    }

    /**
     * Show results section
     */
    showResults() {
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('results-container').style.display = 'block';
    }

    /**
     * Show empty state
     */
    showEmptyState() {
        document.getElementById('empty-state').style.display = 'flex';
        document.getElementById('results-container').style.display = 'none';
    }

    /**
     * Update metrics display
     */
    updateMetrics(summary) {
        document.getElementById('metric-deflection').textContent =
            summary.max_deflection_mm.toFixed(2);
        document.getElementById('metric-stress').textContent =
            summary.max_bending_stress_mpa.toFixed(1);
        document.getElementById('metric-moment').textContent =
            summary.max_moment_knm.toFixed(2);
        document.getElementById('metric-shear').textContent =
            summary.max_shear_kn.toFixed(2);
    }

    /**
     * Render charts from solution data - All in Plotly
     */
    renderCharts(solution, problem) {
        const data = solution.data;
        const x = data.x;
        const isVertical = problem.orientation === 'vertical';

        // Store problem parameters for visualization
        this.lastProblem = problem;
        this.lastSolution = solution;

        // Create all Plotly charts
        this.createDeflectionBeamPlot(data, problem);
        this.createMomentPlot(data, x, isVertical);
        this.createShearPlot(data, x, isVertical);
        this.createDeflectionHeatmap(data, problem);
        this.createStressHeatmap(data);
    }

    /**
     * Create deflected beam shape with proper orientation
     */
    createDeflectionBeamPlot(data, problem) {
        const heatmapEl = document.getElementById('deflection-chart');
        if (!heatmapEl || typeof Plotly === 'undefined') return;

        const isVertical = problem.orientation === 'vertical';
        const length = problem.length;
        const deflection = data.deflection;

        if (isVertical) {
            // For vertical beam: y-axis is position along beam, x-axis is deflection
            const trace = {
                x: deflection.map(v => v * 1000),
                y: data.x,
                mode: 'lines',
                name: 'Deflected Shape',
                line: {
                    color: '#3b82f6',
                    width: 3
                },
                fill: 'tozeroy',
                fillcolor: 'rgba(59, 130, 246, 0.2)'
            };

            const layout = {
                title: 'Vertical Beam - Deflected Shape',
                xaxis: {
                    title: 'Horizontal Deflection (mm)',
                    zeroline: true,
                    zerolinewidth: 2,
                    zerolinecolor: '#000'
                },
                yaxis: {
                    title: 'Height Along Beam (m)',
                    autorange: 'reversed'
                },
                hovermode: 'closest',
                margin: {l: 80, r: 40, t: 80, b: 60}
            };

            Plotly.newPlot(heatmapEl, [trace], layout, {responsive: true});
        } else {
            // For horizontal beam: x-axis is position, y-axis is deflection
            const trace = {
                x: data.x,
                y: deflection.map(v => v * 1000),
                mode: 'lines',
                name: 'Deflected Shape',
                line: {
                    color: '#3b82f6',
                    width: 3
                },
                fill: 'tozeroy',
                fillcolor: 'rgba(59, 130, 246, 0.2)'
            };

            const layout = {
                title: 'Horizontal Beam - Deflected Shape',
                xaxis: {
                    title: 'Position Along Beam (m)'
                },
                yaxis: {
                    title: 'Vertical Deflection (mm)',
                    zeroline: true,
                    zerolinewidth: 2,
                    zerolinecolor: '#000'
                },
                hovermode: 'closest',
                margin: {l: 80, r: 40, t: 80, b: 60}
            };

            Plotly.newPlot(heatmapEl, [trace], layout, {responsive: true});
        }
    }

    /**
     * Create bending moment diagram in Plotly
     */
    createMomentPlot(data, x, isVertical) {
        const el = document.getElementById('moment-chart');
        if (!el || typeof Plotly === 'undefined') return;

        const moment = data.moment.map(v => v / 1000);

        if (isVertical) {
            const trace = {
                x: moment,
                y: x,
                mode: 'lines',
                name: 'Bending Moment',
                line: {color: '#ef4444', width: 2},
                fill: 'tozeroy',
                fillcolor: 'rgba(239, 68, 68, 0.2)'
            };

            const layout = {
                title: 'Bending Moment Diagram',
                xaxis: {title: 'Moment (kN·m)', zeroline: true, zerolinewidth: 2},
                yaxis: {title: 'Height (m)', autorange: 'reversed'},
                hovermode: 'closest',
                margin: {l: 80, r: 40, t: 80, b: 60}
            };

            Plotly.newPlot(el, [trace], layout, {responsive: true});
        } else {
            const trace = {
                x: x,
                y: moment,
                mode: 'lines',
                name: 'Bending Moment',
                line: {color: '#ef4444', width: 2},
                fill: 'tozeroy',
                fillcolor: 'rgba(239, 68, 68, 0.2)'
            };

            const layout = {
                title: 'Bending Moment Diagram',
                xaxis: {title: 'Position (m)'},
                yaxis: {title: 'Moment (kN·m)', zeroline: true, zerolinewidth: 2},
                hovermode: 'closest',
                margin: {l: 80, r: 40, t: 80, b: 60}
            };

            Plotly.newPlot(el, [trace], layout, {responsive: true});
        }
    }

    /**
     * Create shear force diagram in Plotly
     */
    createShearPlot(data, x, isVertical) {
        const el = document.getElementById('shear-chart');
        if (!el || typeof Plotly === 'undefined') return;

        const shear = data.shear.map(v => v / 1000);

        if (isVertical) {
            const trace = {
                x: shear,
                y: x,
                mode: 'lines',
                name: 'Shear Force',
                line: {color: '#10b981', width: 2},
                fill: 'tozeroy',
                fillcolor: 'rgba(16, 185, 129, 0.2)'
            };

            const layout = {
                title: 'Shear Force Diagram',
                xaxis: {title: 'Shear (kN)', zeroline: true, zerolinewidth: 2},
                yaxis: {title: 'Height (m)', autorange: 'reversed'},
                hovermode: 'closest',
                margin: {l: 80, r: 40, t: 80, b: 60}
            };

            Plotly.newPlot(el, [trace], layout, {responsive: true});
        } else {
            const trace = {
                x: x,
                y: shear,
                mode: 'lines',
                name: 'Shear Force',
                line: {color: '#10b981', width: 2},
                fill: 'tozeroy',
                fillcolor: 'rgba(16, 185, 129, 0.2)'
            };

            const layout = {
                title: 'Shear Force Diagram',
                xaxis: {title: 'Position (m)'},
                yaxis: {title: 'Shear (kN)', zeroline: true, zerolinewidth: 2},
                hovermode: 'closest',
                margin: {l: 80, r: 40, t: 80, b: 60}
            };

            Plotly.newPlot(el, [trace], layout, {responsive: true});
        }
    }

    /**
     * Create FEA-style deflection visualization showing deformed beam shape
     */
    createDeflectionHeatmap(data, problem) {
        const heatmapEl = document.getElementById('stress-chart');
        if (!heatmapEl || typeof Plotly === 'undefined') return;

        const isVertical = problem.orientation === 'vertical';
        const length = problem.length || 2.0;
        const height = problem.height || 0.1;
        const width = problem.width || 0.1;

        const x = data.x;
        const deflection = data.deflection;

        // Calculate max deflection for scaling
        const maxDeflection = Math.max(...deflection.map(d => Math.abs(d)));
        const maxDeflectionMm = maxDeflection * 1000;

        // Calculate appropriate scale factor
        // We want deflection to be ~20% of beam length for visibility
        // but not exaggerated
        const targetDeflectionScale = length * 0.15; // 15% of beam length
        const scaleFactor = maxDeflectionMm > 0 ? targetDeflectionScale / maxDeflectionMm : 1;

        // Create undeformed and deformed beam shapes
        // Sample every nth point for clarity
        const sampleRate = Math.max(1, Math.floor(x.length / 30));
        const sampledX = [];
        const sampledDeflection = [];

        for (let i = 0; i < x.length; i += sampleRate) {
            sampledX.push(x[i]);
            // Scale deflection for visualization while keeping proportions
            sampledDeflection.push(deflection[i] * 1000 * scaleFactor); // Convert to mm and scale
        }

        if (isVertical) {
            // Vertical beam: beam height on y, deflection on x
            // Undeformed beam (left edge at x=0)
            const undeformedY = sampledX;
            const undeformedX = Array(sampledX.length).fill(0);

            // Deformed beam (shifted by deflection)
            const deformedX = sampledDeflection;
            const deformedY = sampledX;

            // Create cross-section visualization at multiple points
            const numCrossSections = 5;
            const traces = [];

            // Add undeformed beam outline
            traces.push({
                x: undeformedX,
                y: undeformedY,
                mode: 'lines',
                name: 'Undeformed',
                line: {color: '#ccc', width: 2, dash: 'dash'},
                hoverinfo: 'skip'
            });

            // Add deformed beam shape
            traces.push({
                x: deformedX,
                y: deformedY,
                mode: 'lines+markers',
                name: 'Deformed Shape',
                line: {color: '#3b82f6', width: 3},
                marker: {size: 4},
                fill: 'tozeroy',
                fillcolor: 'rgba(59, 130, 246, 0.15)'
            });

            // Add cross-section rectangles at key points
            for (let i = 0; i < numCrossSections; i++) {
                const idx = Math.floor(i * (sampledX.length - 1) / (numCrossSections - 1));
                const posY = sampledX[idx];
                const deflX = sampledDeflection[idx];

                // Draw rectangle showing cross-section at this position
                // Scale cross-section size proportionally for visibility
                const sectionScale = Math.max(width, height) * 2; // Make sections visible
                const halfHeight = (height * sectionScale) / length;
                const halfWidth = (width * sectionScale) / length;
                const xRect = [deflX - halfWidth, deflX + halfWidth, deflX + halfWidth, deflX - halfWidth, deflX - halfWidth];
                const yRect = [posY - halfHeight, posY - halfHeight, posY + halfHeight, posY + halfHeight, posY - halfHeight];

                traces.push({
                    x: xRect,
                    y: yRect,
                    mode: 'lines',
                    line: {color: '#ef4444', width: 1},
                    fill: 'toself',
                    fillcolor: 'rgba(239, 68, 68, 0.1)',
                    hoverinfo: 'skip',
                    showlegend: false
                });
            }

            // Create annotations for point loads
            const annotations = [];
            if (problem.point_loads && problem.point_loads.length > 0) {
                const maxDeflectionMm = maxDeflection * 1000;
                const arrowWidth = maxDeflectionMm * scaleFactor * 0.3; // 30% of scaled max deflection

                problem.point_loads.forEach(load => {
                    const loadPos = load.position * length;
                    const arrowColor = load.direction === 'downward' ? '#f97316' : '#8b5cf6'; // orange for down, purple for up

                    annotations.push({
                        y: loadPos,
                        x: arrowWidth,
                        xref: 'x',
                        yref: 'y',
                        text: `${load.magnitude}kN`,
                        showarrow: true,
                        arrowhead: load.direction === 'downward' ? 3 : 2,
                        arrowsize: 2,
                        arrowwidth: 3,
                        arrowcolor: arrowColor,
                        ax: load.direction === 'downward' ? 50 : -50,
                        ay: 0,
                        font: {color: arrowColor, size: 11},
                        align: 'center',
                        bgcolor: 'rgba(255,255,255,0.7)',
                        bordercolor: arrowColor,
                        borderwidth: 1,
                        borderpad: 4
                    });
                });
            }

            const layout = {
                title: 'Vertical Beam - Deformed Shape with Cross-Sections (1:1 Scale)',
                xaxis: {
                    title: 'Horizontal Deflection (mm)',
                    zeroline: true,
                    zerolinewidth: 2,
                    scaleanchor: 'y',
                    scaleratio: 1
                },
                yaxis: {
                    title: 'Height Along Beam (m)',
                    autorange: 'reversed',
                    scaleanchor: 'x',
                    scaleratio: 1
                },
                hovermode: 'closest',
                margin: {l: 80, r: 40, t: 80, b: 60},
                annotations: annotations
            };

            Plotly.newPlot(heatmapEl, traces, layout, {responsive: true});
        } else {
            // Horizontal beam: position on x, deflection on y
            // Undeformed beam (along x-axis at y=0)
            const undeformedY = Array(sampledX.length).fill(0);

            // Deformed beam (y-axis shows deflection)
            const deformedX = sampledX;
            const deformedY = sampledDeflection;

            // Create cross-section visualization at multiple points
            const numCrossSections = 5;
            const traces = [];

            // Add undeformed beam outline
            traces.push({
                x: sampledX,
                y: undeformedY,
                mode: 'lines',
                name: 'Undeformed',
                line: {color: '#ccc', width: 2, dash: 'dash'},
                hoverinfo: 'skip'
            });

            // Add deformed beam shape
            traces.push({
                x: deformedX,
                y: deformedY,
                mode: 'lines+markers',
                name: 'Deformed Shape',
                line: {color: '#3b82f6', width: 3},
                marker: {size: 4},
                fill: 'tozeroy',
                fillcolor: 'rgba(59, 130, 246, 0.15)'
            });

            // Add cross-section rectangles at key points
            for (let i = 0; i < numCrossSections; i++) {
                const idx = Math.floor(i * (sampledX.length - 1) / (numCrossSections - 1));
                const posX = sampledX[idx];
                const deflY = sampledDeflection[idx];

                // Draw rectangle showing cross-section at this position
                // Scale cross-section size proportionally for visibility
                const sectionScale = Math.max(width, height) * 2; // Make sections visible
                const halfHeight = (height * sectionScale) / length;
                const halfWidth = (width * sectionScale) / length;
                const xRect = [posX - halfWidth, posX + halfWidth, posX + halfWidth, posX - halfWidth, posX - halfWidth];
                const yRect = [deflY - halfHeight, deflY - halfHeight, deflY + halfHeight, deflY + halfHeight, deflY - halfHeight];

                traces.push({
                    x: xRect,
                    y: yRect,
                    mode: 'lines',
                    line: {color: '#ef4444', width: 1},
                    fill: 'toself',
                    fillcolor: 'rgba(239, 68, 68, 0.1)',
                    hoverinfo: 'skip',
                    showlegend: false
                });
            }

            // Create annotations for point loads
            const annotations = [];
            if (problem.point_loads && problem.point_loads.length > 0) {
                const maxDeflectionMm = maxDeflection * 1000;
                const arrowHeight = maxDeflectionMm * scaleFactor * 0.3; // 30% of scaled max deflection

                problem.point_loads.forEach(load => {
                    const loadPos = load.position * length;
                    const arrowColor = load.direction === 'downward' ? '#f97316' : '#8b5cf6'; // orange for down, purple for up

                    annotations.push({
                        x: loadPos,
                        y: arrowHeight,
                        xref: 'x',
                        yref: 'y',
                        text: `${load.magnitude}kN`,
                        showarrow: true,
                        arrowhead: load.direction === 'downward' ? 2 : 3,
                        arrowsize: 2,
                        arrowwidth: 3,
                        arrowcolor: arrowColor,
                        ax: 0,
                        ay: load.direction === 'downward' ? 50 : -50,
                        font: {color: arrowColor, size: 11},
                        align: 'center',
                        bgcolor: 'rgba(255,255,255,0.7)',
                        bordercolor: arrowColor,
                        borderwidth: 1,
                        borderpad: 4
                    });
                });
            }

            const layout = {
                title: 'Horizontal Beam - Deformed Shape with Cross-Sections (1:1 Scale)',
                xaxis: {
                    title: 'Position Along Beam (m)',
                    scaleanchor: 'y',
                    scaleratio: 1
                },
                yaxis: {
                    title: 'Vertical Deflection (mm)',
                    zeroline: true,
                    zerolinewidth: 2,
                    scaleanchor: 'x',
                    scaleratio: 1
                },
                hovermode: 'closest',
                margin: {l: 80, r: 40, t: 80, b: 60},
                annotations: annotations
            };

            Plotly.newPlot(heatmapEl, traces, layout, {responsive: true});
        }
    }

    /**
     * Create stress distribution heatmap across beam section using Plotly
     */
    createStressHeatmap(data) {
        const heatmapEl = document.getElementById('stress-heatmap');
        if (!heatmapEl || typeof Plotly === 'undefined') return;

        // Use stored problem parameters
        const problem = this.lastProblem || {};

        // Create synthetic stress distribution across section
        // Maximum bending stress occurs at top/bottom fibers
        const sectionHeight = problem.height || 0.1;
        const sectionWidth = problem.width || 0.1;

        // Create grid for heatmap: position along beam vs height
        const numHeightPoints = 11;
        const heights = Array.from({length: numHeightPoints}, (_, i) =>
            (i / (numHeightPoints - 1)) * sectionHeight - sectionHeight / 2
        );

        // Sample stress at different positions
        const stressSamples = [];
        for (let i = 0; i < Math.min(data.bending_stress.length, 20); i++) {
            const idx = Math.floor(i * (data.bending_stress.length - 1) / 19);
            const maxStress = data.bending_stress[idx] / 1e6;

            // Stress varies linearly across section (bending theory)
            const stressRow = heights.map(h => {
                return (h / (sectionHeight / 2)) * maxStress;
            });
            stressSamples.push(stressRow);
        }

        const trace = {
            z: stressSamples,
            type: 'heatmap',
            colorscale: 'Viridis',
            colorbar: {
                title: 'Stress (MPa)'
            }
        };

        const layout = {
            title: 'Bending Stress Distribution Across Section',
            xaxis: {
                title: 'Section Height'
            },
            yaxis: {
                title: 'Position Along Beam'
            },
            margin: {l: 60, r: 60, t: 80, b: 60}
        };

        const config = {
            responsive: true,
            displayModeBar: true
        };

        Plotly.newPlot(heatmapEl, [trace], layout, config);
    }


    /**
     * Populate summary table
     */
    populateSummaryTable(summary, parameters) {
        const tbody = document.getElementById('summary-tbody');
        if (!tbody) return;

        const rows = [
            ['Property', 'Value'],
            ['Beam Length', `${parameters.length.toFixed(2)} m`],
            ['Section Width', `${parameters.width.toFixed(3)} m`],
            ['Section Height', `${parameters.height.toFixed(3)} m`],
            ['Material', parameters.material],
            ['Orientation', parameters.orientation],
            ['End Condition', parameters.end_condition.replace(/_/g, ' ')],
            ['Axial Load', `${parameters.axial_load.toFixed(1)} kN`],
            ['Lateral Load', `${parameters.lateral_load.toFixed(1)} kN/m`],
            ['', ''],
            ['Max Deflection', `${summary.max_deflection_mm.toFixed(2)} mm`],
            ['Max Moment', `${summary.max_moment_knm.toFixed(2)} kN·m`],
            ['Max Shear', `${summary.max_shear_kn.toFixed(2)} kN`],
            ['Max Bending Stress', `${summary.max_bending_stress_mpa.toFixed(1)} MPa`],
            ['Max Axial Stress', `${summary.max_axial_stress_mpa.toFixed(1)} MPa`],
            ['Critical Buckling Load', `${summary.critical_buckling_load_kn.toFixed(1)} kN`],
        ];

        tbody.innerHTML = rows.slice(1).map(([prop, val]) => {
            if (prop === '') return '<tr><td colspan="2">&nbsp;</td></tr>';
            return `<tr><td><strong>${prop}</strong></td><td>${val}</td></tr>`;
        }).join('');
    }

    /**
     * Populate data table
     */
    populateDataTable(solution) {
        const tbody = document.getElementById('results-tbody');
        if (!tbody) return;

        const data = solution.data;
        const rows = [];

        for (let i = 0; i < data.x.length; i++) {
            rows.push(`
                <tr>
                    <td>${data.x[i].toFixed(3)}</td>
                    <td>${(data.deflection[i] * 1000).toFixed(2)}</td>
                    <td>${(data.moment[i] / 1000).toFixed(2)}</td>
                    <td>${(data.shear[i] / 1000).toFixed(2)}</td>
                    <td>${(data.bending_stress[i] / 1e6).toFixed(2)}</td>
                    <td>${(data.axial_stress[i] / 1e6).toFixed(2)}</td>
                </tr>
            `);
        }

        tbody.innerHTML = rows.join('');
    }

    /**
     * Export data to CSV
     */
    exportToCSV() {
        if (!appState.solution) return;

        const data = appState.solution.data;
        const rows = [
            ['Position (m)', 'Deflection (mm)', 'Moment (kN·m)', 'Shear (kN)',
             'Bending Stress (MPa)', 'Axial Stress (MPa)']
        ];

        for (let i = 0; i < data.x.length; i++) {
            rows.push([
                data.x[i].toFixed(3),
                (data.deflection[i] * 1000).toFixed(2),
                (data.moment[i] / 1000).toFixed(2),
                (data.shear[i] / 1000).toFixed(2),
                (data.bending_stress[i] / 1e6).toFixed(2),
                (data.axial_stress[i] / 1e6).toFixed(2)
            ]);
        }

        const csv = rows.map(r => r.join(',')).join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'beam_column_results.csv';
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Show status message
     */
    showStatus(message, type = 'info') {
        const statusEl = document.getElementById('status-message');
        if (!statusEl) return;

        statusEl.textContent = message;
        statusEl.className = `status-message ${type}`;

        if (type !== 'loading') {
            setTimeout(() => {
                statusEl.className = 'status-message';
            }, 3000);
        }
    }

    /**
     * Show loading state on solve button
     */
    setSolveButtonLoading(isLoading) {
        const btn = document.getElementById('solve-btn');
        if (!btn) return;

        btn.disabled = isLoading;
        btn.classList.toggle('loading', isLoading);
        btn.textContent = isLoading ? '⏳ Solving...' : '🔧 Solve Problem';
    }

    /**
     * Handle solve button click
     */
    async onSolveClick() {
        if (appState.isLoading) return;

        appState.setLoading(true);
        this.setSolveButtonLoading(true);
        this.showStatus('Solving beam-column equations...', 'loading');

        try {
            const params = appState.getParameters();
            const solution = await BeamAPI.solveProblem(params);

            appState.setSolution(solution);
            this.displayResults(solution);
            this.showStatus('Solution complete!', 'success');
        } catch (error) {
            appState.setError(error.message);
            this.showStatus(`Error: ${error.message}`, 'error');
            console.error('Solve error:', error);
        } finally {
            appState.setLoading(false);
            this.setSolveButtonLoading(false);
        }
    }

    /**
     * Display all results
     */
    displayResults(solution) {
        this.showResults();
        this.updateMetrics(solution.summary);
        this.renderCharts(solution, appState.parameters);
        this.populateSummaryTable(solution.summary, appState.parameters);
        this.populateDataTable(solution);
        this.switchTab('charts');
    }
}

// Initialize UI when DOM is ready
let ui = null;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        ui = new UI();
        ui.renderPointLoads();
    });
} else {
    ui = new UI();
    ui.renderPointLoads();
}
