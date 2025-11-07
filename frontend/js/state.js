/**
 * State Management for Beam-Column Simulator
 * Manages UI state, form parameters, and solutions
 */

class AppState {
    constructor() {
        this.parameters = {
            length: 2.0,
            width: 0.1,
            height: 0.1,
            material: 'Steel',
            orientation: 'horizontal',
            end_condition: 'cantilever',
            include_self_weight: true,
            axial_load: 50,
            lateral_load: 10,
            point_loads: [
                {
                    magnitude: 25.0,
                    position: 0.2,
                    direction: 'downward'
                },
                {
                    magnitude: 25.0,
                    position: 0.8,
                    direction: 'upward'
                }
            ]
        };

        this.solution = null;
        this.isLoading = false;
        this.error = null;
        this.lastParametersHash = null;

        // Initialize state from DOM if it exists
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this._initFromDOM());
        } else {
            this._initFromDOM();
        }
    }

    /**
     * Initialize parameters from DOM elements
     */
    _initFromDOM() {
        if (!document.getElementById('length')) return;

        this.parameters.length = parseFloat(document.getElementById('length').value);
        this.parameters.width = parseFloat(document.getElementById('width').value);
        this.parameters.height = parseFloat(document.getElementById('height').value);
        this.parameters.material = document.getElementById('material').value;
        this.parameters.orientation = document.querySelector('input[name="orientation"]:checked').value;
        this.parameters.end_condition = document.getElementById('end-condition').value;
        this.parameters.include_self_weight = document.getElementById('self-weight').checked;
        this.parameters.axial_load = parseFloat(document.getElementById('axial-load').value);
        this.parameters.lateral_load = parseFloat(document.getElementById('lateral-load').value);
    }

    /**
     * Get current parameters for API call
     */
    getParameters() {
        return {
            ...this.parameters,
            point_loads: this.parameters.point_loads.filter(pl => pl.magnitude > 0)
        };
    }

    /**
     * Update a single parameter
     */
    updateParameter(key, value) {
        this.parameters[key] = value;
        this.invalidateSolution();
    }

    /**
     * Update multiple parameters
     */
    updateParameters(updates) {
        Object.assign(this.parameters, updates);
        this.invalidateSolution();
    }

    /**
     * Add point load
     */
    addPointLoad() {
        if (this.parameters.point_loads.length < 5) {
            this.parameters.point_loads.push({
                magnitude: 5.0,
                position: 0.5,
                direction: 'downward'
            });
            this.invalidateSolution();
        }
    }

    /**
     * Remove point load by index
     */
    removePointLoad(index) {
        if (index >= 0 && index < this.parameters.point_loads.length) {
            this.parameters.point_loads.splice(index, 1);
            this.invalidateSolution();
        }
    }

    /**
     * Update point load by index
     */
    updatePointLoad(index, updates) {
        if (index >= 0 && index < this.parameters.point_loads.length) {
            Object.assign(this.parameters.point_loads[index], updates);
            this.invalidateSolution();
        }
    }

    /**
     * Set number of point loads
     */
    setNumPointLoads(count) {
        count = Math.max(0, Math.min(5, parseInt(count)));

        // Add new loads if count increased
        while (this.parameters.point_loads.length < count) {
            this.parameters.point_loads.push({
                magnitude: 5.0,
                position: 0.5,
                direction: 'downward'
            });
        }

        // Remove loads if count decreased
        this.parameters.point_loads = this.parameters.point_loads.slice(0, count);
        this.invalidateSolution();
    }

    /**
     * Set solution data
     */
    setSolution(solution) {
        this.solution = solution;
        this.error = null;
        this.lastParametersHash = this._hashParameters();
    }

    /**
     * Invalidate solution (mark as stale)
     */
    invalidateSolution() {
        this.solution = null;
    }

    /**
     * Check if solution is still valid for current parameters
     */
    isSolutionValid() {
        if (!this.solution) return false;
        return this._hashParameters() === this.lastParametersHash;
    }

    /**
     * Create hash of parameters for comparison
     */
    _hashParameters() {
        return JSON.stringify(this.getParameters());
    }

    /**
     * Set loading state
     */
    setLoading(isLoading) {
        this.isLoading = isLoading;
    }

    /**
     * Set error
     */
    setError(error) {
        this.error = error;
    }

    /**
     * Clear error
     */
    clearError() {
        this.error = null;
    }

    /**
     * Reset to initial state
     */
    reset() {
        this.solution = null;
        this.error = null;
        this.lastParametersHash = null;
        this.isLoading = false;
    }
}

// Global state instance
const appState = new AppState();
