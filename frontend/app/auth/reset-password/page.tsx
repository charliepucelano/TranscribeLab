"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { Button, Input } from '@/components/ui';
import styles from '../auth.module.css';

export default function ResetPasswordPage() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [recoveryKey, setRecoveryKey] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (newPassword.length < 8) {
            setError("New password must be at least 8 characters");
            return;
        }

        setLoading(true);

        try {
            await api.post('/auth/reset-password', {
                email,
                recovery_key: recoveryKey,
                new_password: newPassword
            });
            setSuccess(true);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Reset failed. Check your Recovery Key.');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className={styles.container}>
                <div className={styles.card}>
                    <h1 className={styles.title} style={{ color: '#22c55e' }}>Password Reset!</h1>
                    <p className={styles.subtitle}>Your password has been updated securely.</p>
                    <Button onClick={() => router.push('/auth/login')} fullWidth>
                        Exceed to Login
                    </Button>
                </div>
            </div>
        )
    }

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h1 className={styles.title}>Reset Password</h1>
                <p className={styles.subtitle}>Enter your Recovery Key to restore access.</p>

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
                        label="Recovery Key"
                        type="text"
                        placeholder="Enter your long recovery string..."
                        value={recoveryKey}
                        onChange={(e) => setRecoveryKey(e.target.value)}
                        required
                    />

                    <Input
                        label="New Password"
                        type="password"
                        placeholder="••••••••"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                    />

                    <Button type="submit" fullWidth disabled={loading}>
                        {loading ? 'Recover Account' : 'Reset Password'}
                    </Button>
                </form>

                <div className={styles.footer}>
                    <Link href="/auth/login" className={styles.link}>
                        Back to Login
                    </Link>
                </div>
            </div>
        </div>
    );
}
