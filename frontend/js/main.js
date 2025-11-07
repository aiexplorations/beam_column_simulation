/**
 * Main entry point for Beam-Column Simulator frontend
 * Initializes the application and handles startup
 */

class BeamApp {
    constructor() {
        this.isInitialized = false;
        this.init();
    }

    async init() {
        console.log('Initializing Beam-Column Simulator...');

        try {
            // Check backend connectivity
            const healthCheck = await BeamAPI.healthCheck();
            if (!healthCheck) {
                console.warn('Backend not available. Some features may not work.');
                ui.showStatus('⚠️ Backend server not reachable at http://localhost:5000', 'error');
                return;
            }

            console.log('Backend is healthy');
            this.isInitialized = true;
            ui.showEmptyState();
        } catch (error) {
            console.error('Initialization error:', error);
            ui.showStatus('Failed to initialize application', 'error');
        }
    }

    /**
     * Get current problem definition for display
     */
    getProblemDefinition() {
        const params = appState.getParameters();
        return {
            geometry: {
                length: params.length,
                width: params.width,
                height: params.height
            },
            material: params.material,
            orientation: params.orientation,
            end_condition: params.end_condition,
            loads: {
                axial: params.axial_load,
                lateral: params.lateral_load,
                point_loads: params.point_loads
            },
            self_weight: params.include_self_weight
        };
    }
}

// Initialize app when DOM is ready
let app = null;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        app = new BeamApp();
    });
} else {
    app = new BeamApp();
}

// Setup keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to solve
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const solveBtn = document.getElementById('solve-btn');
        if (solveBtn && !solveBtn.disabled) {
            solveBtn.click();
        }
    }
});

// Log app state for debugging
window.appState = appState;
window.BeamAPI = BeamAPI;
