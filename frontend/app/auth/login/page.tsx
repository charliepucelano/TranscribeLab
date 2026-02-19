"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button, Input } from '@/components/ui';
import styles from '../auth.module.css';
import { Eye, EyeOff } from 'lucide-react';

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            // Use URLSearchParams for OAuth2PasswordRequestForm compatibility if needed, 
            // but standard FASTAPI OAuth2PasswordRequestForm expects form data.
            // However, usually we can send JSON if we adjust backend OR send FormData.
            // Let's check backend: `form_data: OAuth2PasswordRequestForm = Depends()`
            // This STRICTLY expects form-data 'username' and 'password'.

            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const response = await api.post('/auth/token', formData);

            const { access_token } = response.data;
            if (access_token) {
                localStorage.setItem('token', access_token);
                router.push('/dashboard');
            }
        } catch (err: any) {
            console.error(err);
            let errorMessage = 'Login failed. Please check your credentials.';
            if (err.response?.data?.detail) {
                if (typeof err.response.data.detail === 'string') {
                    errorMessage = err.response.data.detail;
                } else if (Array.isArray(err.response.data.detail)) {
                    // Handle Pydantic validation errors
                    errorMessage = err.response.data.detail.map((e: any) => e.msg).join(', ');
                } else if (typeof err.response.data.detail === 'object') {
                    errorMessage = JSON.stringify(err.response.data.detail);
                }
            }
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h1 className={styles.title}>Welcome Back</h1>
                <p className={styles.subtitle}>Enter your credentials to access your account</p>

                <form onSubmit={handleSubmit} className={styles.form}>
                    {error && <div style={{ color: 'hsl(var(--destructive))', fontSize: '0.875rem', textAlign: 'center' }}>{error}</div>}

                    <Input
                        label="Username"
                        type="text"
                        placeholder="username"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />

                    <div style={{ position: 'relative' }}>
                        <Input
                            label="Password"
                            type={showPassword ? "text" : "password"}
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            style={{
                                position: 'absolute',
                                right: '10px',
                                top: '38px',
                                background: 'none',
                                border: 'none',
                                color: '#666',
                                cursor: 'pointer'
                            }}
                        >
                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                    </div>

                    <Button type="submit" fullWidth disabled={loading}>
                        {loading ? 'Signing in...' : 'Sign In'}
                    </Button>
                </form>

                <div className={styles.footer}>
                    Don't have an account?{' '}
                    <Link href="/auth/register" className={styles.link}>
                        Sign up
                    </Link>
                </div>
            </div>
        </div>
    );
}
