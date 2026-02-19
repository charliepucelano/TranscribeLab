
"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button, Input } from '@/components/ui';
import styles from '../auth.module.css';
import { Eye, EyeOff, Lock, Check } from 'lucide-react';

export default function ChangePasswordPage() {
    const router = useRouter();
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

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
            await api.post('/auth/update-password', {
                new_password: password
            });
            // Redirect to dashboard on success
            router.push('/dashboard');
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Failed to update password.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <div className="flex justify-center mb-4 text-yellow-500">
                    <Lock size={48} />
                </div>
                <h1 className={styles.title}>Change Password Required</h1>
                <p className={styles.subtitle}>
                    Your account has been reset. Please set a new secure password to continue.
                </p>

                <form onSubmit={handleSubmit} className={styles.form}>
                    {error && <div className="text-red-500 text-sm text-center mb-4">{error}</div>}

                    <div style={{ position: 'relative' }}>
                        <Input
                            label="New Password"
                            type={showPassword ? "text" : "password"}
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-[38px] text-gray-500 hover:text-gray-300"
                        >
                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                    </div>

                    <Input
                        label="Confirm New Password"
                        type={showPassword ? "text" : "password"}
                        placeholder="••••••••"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                    />

                    <Button type="submit" fullWidth disabled={loading}>
                        {loading ? 'Updating...' : 'Set New Password'}
                    </Button>
                </form>
            </div>
        </div>
    );
}
