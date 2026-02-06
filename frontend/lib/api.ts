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
        if (typeof window !== 'undefined') {
            const token = localStorage.getItem('token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
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
