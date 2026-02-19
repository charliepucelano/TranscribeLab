"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button, Input } from '@/components/ui';
import styles from '../auth.module.css';
import { Eye, EyeOff } from 'lucide-react';

export default function RegisterPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [recoveryKey, setRecoveryKey] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (password.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }

        setLoading(true);

        try {
            // 1. Register
            const registerResponse = await api.post('/auth/register', {
                email,
                password
            });

            // 2. Auto-Login (Get Token)
            try {
                const formData = new FormData();
                formData.append('username', email);
                formData.append('password', password);

                // Removing Content-Type header is handled by interceptor now
                const loginResponse = await api.post('/auth/token', formData);

                if (loginResponse.data?.access_token) {
                    localStorage.setItem('token', loginResponse.data.access_token);
                }
            } catch (loginErr) {
                console.error("Auto-login failed:", loginErr);
                // We don't stop the flow, user can login manually later if needed, 
                // but we still show recovery key.
            }

            // 3. Show recovery key
            if (registerResponse.data && registerResponse.data.recovery_key) {
                setRecoveryKey(registerResponse.data.recovery_key);
            } else {
                router.push('/dashboard');
            }

        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleDashboardRedirect = () => {
        // Token should be in localStorage from auto-login
        router.push('/dashboard');
    }

    if (recoveryKey) {
        return (
            <div className={styles.container}>
                <div className={styles.card} style={{ maxWidth: '600px' }}>
                    <h1 className={styles.title} style={{ color: '#22c55e' }}>Registration Successful!</h1>
                    <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 my-6 text-left">
                        <h3 className="text-red-400 font-bold mb-2">⚠️ IMPORTANT: SAVE THIS RECOVERY KEY</h3>
                        <p className="text-sm text-gray-300 mb-4">
                            This is the <strong>ONLY</strong> way to recover your account if you forget your password.
                            We cannot reset your password for you because your data is encrypted.
                        </p>
                        <div className="bg-black/50 p-3 rounded font-mono text-center text-lg tracking-wider break-all text-yellow-500 select-all border border-white/10">
                            {recoveryKey}
                        </div>
                    </div>

                    <Button onClick={handleDashboardRedirect} fullWidth variant="secondary">
                        I have saved my Recovery Key. Proceed to Dashboard.
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h1 className={styles.title}>Create Account</h1>
                <p className={styles.subtitle}>Start transcribing your meetings today</p>

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

                    <Input
                        label="Confirm Password"
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                    />

                    <p style={{ fontSize: '0.75rem', color: '#888', marginTop: '-0.5rem', marginBottom: '1rem', lineHeight: '1.4' }}>
                        Your data is <strong>encrypted and securely stored on your private server</strong>.
                    </p>

                    <Button type="submit" fullWidth disabled={loading}>
                        {loading ? 'Creating account...' : 'Create Account'}
                    </Button>
                </form>

                <div className={styles.footer}>
                    Already have an account?{' '}
                    <Link href="/auth/login" className={styles.link}>
                        Sign in
                    </Link>
                </div>
            </div>
        </div>
    );
}
