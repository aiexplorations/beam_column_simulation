/**
 * API Client for Beam-Column Simulator Backend
 * Handles all communication with the FastAPI server
 */

// Configure backend URL - can be overridden via window.API_BASE_URL
const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8888';

class BeamAPI {
    /**
     * Fetch available materials from the backend
     */
    static async getMaterials() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/materials`);
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            const data = await response.json();
            return data.materials;
        } catch (error) {
            console.error('Error fetching materials:', error);
            throw error;
        }
    }

    /**
     * Solve the beam-column problem with given parameters
     * @param {Object} params - Problem parameters
     * @returns {Object} Solution data
     */
    static async solveProblem(params) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/solve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `API error: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('Error solving problem:', error);
            throw error;
        }
    }

    /**
     * Health check endpoint
     */
    static async healthCheck() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }
}
