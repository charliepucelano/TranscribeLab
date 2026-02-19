"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui';
import styles from './settings.module.css';
import { Shield, LogOut } from 'lucide-react';

export default function SettingsPage() {
    const router = useRouter();
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const res = await api.get('/auth/me');
                setUser(res.data);
            } catch (error) {
                console.error("Failed to fetch user", error);
            } finally {
                setLoading(false);
            }
        };
        fetchUser();
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        router.push('/auth/login');
    };

    const [showRecoveryModal, setShowRecoveryModal] = useState(false);
    const [passwordConfirm, setPasswordConfirm] = useState('');
    const [recoveryKey, setRecoveryKey] = useState('');
    const [keyLoading, setKeyLoading] = useState(false);
    const [keyError, setKeyError] = useState('');

    const handleViewRecoveryKey = async () => {
        setKeyError('');
        setKeyLoading(true);
        try {
            const res = await api.post('/auth/recovery-key', { password: passwordConfirm });
            setRecoveryKey(res.data.recovery_key);
        } catch (e: any) {
            setKeyError(e.response?.data?.detail || "Invalid password");
        } finally {
            setKeyLoading(false);
        }
    };

    const closeRecoveryModal = () => {
        setShowRecoveryModal(false);
        setPasswordConfirm('');
        setRecoveryKey('');
        setKeyError('');
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Settings</h1>

            {loading ? (
                <p>Loading...</p>
            ) : (
                <>
                    {/* Admin Section */}
                    {user?.is_superuser && (
                        <section className={styles.section} style={{ borderColor: '#22c55e' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: '#22c55e' }}>
                                <Shield size={24} />
                                <h2 style={{ margin: 0, color: '#22c55e' }}>Admin Controls</h2>
                            </div>
                            <p>You have superuser privileges.</p>
                            <Link href="/admin">
                                <Button className="mt-4">
                                    Go to Admin Dashboard
                                </Button>
                            </Link>
                        </section>
                    )}

                    <section className={styles.section}>
                        <h2>Account</h2>
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', fontSize: '0.875rem', color: '#888', marginBottom: '0.25rem' }}>Email</label>
                            <div style={{ padding: '0.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                                {user?.email}
                            </div>
                        </div>

                        <div className="mt-6 mb-6 p-4 border border-yellow-500/20 bg-yellow-900/10 rounded-lg">
                            <h3 className="text-yellow-500 font-bold mb-2">Security</h3>
                            <Button
                                variant="secondary"
                                onClick={() => setShowRecoveryModal(true)}
                                className="w-full"
                            >
                                View Recovery Key
                            </Button>
                        </div>

                        <Button variant="secondary" onClick={handleLogout} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ef4444', borderColor: '#ef4444' }}>
                            <LogOut size={16} />
                            Sign Out
                        </Button>
                    </section>
                </>
            )}

            {/* Recovery Key Modal */}
            {showRecoveryModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-[#1a1a1a] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl animate-in zoom-in-95 duration-200">
                        <h3 className="text-xl font-bold text-white mb-4">View Recovery Key</h3>

                        <form onSubmit={(e) => { e.preventDefault(); handleViewRecoveryKey(); }}>
                            {!recoveryKey ? (
                                <>
                                    <p className="text-gray-400 mb-4 text-sm">
                                        Please enter your password to decrypt and view your Recovery Key.
                                    </p>
                                    {keyError && (
                                        <div className="bg-red-900/20 border border-red-500/50 p-3 rounded mb-4 text-sm">
                                            <p className="text-red-400 font-bold mb-1">Access Denied</p>
                                            <p className="text-gray-300">
                                                {keyError.includes("Failed to retrieve") || keyError.includes("500")
                                                    ? "Your encryption key is out of sync. This happens if your password was reset by an Admin. You cannot view the old key because it is locked with your old password."
                                                    : keyError}
                                            </p>
                                        </div>
                                    )}
                                    <input
                                        type="password"
                                        placeholder="Current Password"
                                        value={passwordConfirm}
                                        onChange={(e) => setPasswordConfirm(e.target.value)}
                                        className="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 mb-6"
                                        autoFocus
                                    />
                                    <div className="flex justify-end gap-3">
                                        <Button type="button" variant="secondary" onClick={closeRecoveryModal}>Cancel</Button>
                                        <Button type="submit" disabled={!passwordConfirm || keyLoading}>
                                            {keyLoading ? 'Decrypting...' : 'Reveal Key'}
                                        </Button>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <p className="text-green-400 font-bold mb-2">Recovery Key Decrypted:</p>
                                    <div className="bg-black p-4 rounded border border-green-500/30 font-mono text-lg text-yellow-500 break-all select-all mb-6">
                                        {recoveryKey}
                                    </div>
                                    <Button type="button" onClick={closeRecoveryModal} fullWidth>Close</Button>
                                </>
                            )}
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
