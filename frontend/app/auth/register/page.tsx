"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button, Input } from '@/components/ui';
import styles from '../auth.module.css';

export default function RegisterPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
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
            // Register
            const response = await api.post('/auth/register', {
                email,
                password
            });

            // Show recovery key
            if (response.data && response.data.recovery_key) {
                setRecoveryKey(response.data.recovery_key);
            } else {
                // Fallback if no key returned (shouldn't happen with new backend)
                router.push('/auth/login');
            }

        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleLoginRedirect = () => {
        router.push('/auth/login');
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

                    <Button onClick={handleLoginRedirect} fullWidth variant="secondary">
                        I have saved my Recovery Key. Proceed to Login.
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

                    <Input
                        label="Confirm Password"
                        type="password"
                        placeholder="••••••••"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                    />

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
