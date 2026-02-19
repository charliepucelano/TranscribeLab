import axios from 'axios';

const api = axios.create({
    baseURL: '/api', // Relative path to use Next.js rewrites
    timeout: 600000, // 10 minutes (matching backend)
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add token
api.interceptors.request.use(
    (config) => {
        // Remove Content-Type for FormData to let browser set boundary
        if (config.data instanceof FormData) {
            if (config.headers.delete) {
                config.headers.delete('Content-Type');
            } else {
                delete config.headers['Content-Type'];
            }
        }

        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('token');
            if (token) {
                // Ensure headers object exists
                if (!config.headers) {
                    config.headers = {} as any;
                }

                // Use safe setting method if available (Axios 1.x+) or direct assignment
                if (config.headers.set) {
                    config.headers.set('Authorization', `Bearer ${token}`);
                } else {
                    config.headers['Authorization'] = `Bearer ${token}`;
                }
                // console.log(`[API] Attaching token to ${config.url}`);
            } else {
                console.warn("[API] No token in localStorage for request:", config.url);
            }
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor to handle 401
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            console.error("[API] 401 Unauthorized received. Logging out.");
            if (typeof window !== 'undefined') {
                localStorage.removeItem('token');
                // Optionally redirect to login
                if (!window.location.pathname.startsWith('/auth')) {
                    window.location.href = '/auth/login';
                }
            }
        }
        return Promise.reject(error);
    }
);

export default api;
