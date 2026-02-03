"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button, Input } from '@/components/ui';
import styles from '../auth.module.css';

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

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

            const response = await api.post('/auth/token', formData, {
                headers: { 'Content-Type': 'multipart/form-data' } // Axios handles boundary
            });

            const { access_token } = response.data;
            if (access_token) {
                localStorage.setItem('token', access_token);
                router.push('/dashboard');
            }
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
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
                        label="Email"
                        type="email"
                        placeholder="name@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />

                    <Input
                        label="Password"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />

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
