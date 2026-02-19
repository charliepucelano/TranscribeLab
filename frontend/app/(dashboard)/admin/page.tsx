"use client";

import React, { useEffect, useState } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui';
import { Loader2, User as UserIcon, FileAudio, RefreshCw, AlertTriangle, Trash2, X, Check, Shield } from 'lucide-react';

export default function AdminPage() {
    const [users, setUsers] = useState<any[]>([]);
    const [jobs, setJobs] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Modal States
    const [resetModalUser, setResetModalUser] = useState<any>(null);
    const [newPassword, setNewPassword] = useState('');

    const [deleteModalUser, setDeleteModalUser] = useState<any>(null);

    const fetchData = async () => {
        setLoading(true);
        setError('');
        try {
            const [usersRes, jobsRes] = await Promise.all([
                api.get('/admin/users'),
                api.get('/admin/jobs')
            ]);
            setUsers(usersRes.data);
            setJobs(jobsRes.data);
        } catch (err: any) {
            console.error("Failed to fetch admin data", err);
            setError("Failed to load admin data. ensure you are an admin.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleResetPasswordSubmit = async () => {
        if (!resetModalUser || !newPassword) return;
        try {
            await api.post(`/admin/users/${resetModalUser.id || resetModalUser._id}/reset-password`, {
                new_password: newPassword
            });
            alert("Password reset successfully.");
            setResetModalUser(null);
            setNewPassword("");
        } catch (e: any) {
            alert("Failed to reset password: " + (e.response?.data?.detail || e.message));
        }
    };

    const handleDeleteUserSubmit = async () => {
        if (!deleteModalUser) return;
        try {
            await api.delete(`/admin/users/${deleteModalUser.id || deleteModalUser._id}`);
            alert("User deleted successfully.");
            setDeleteModalUser(null);
            fetchData(); // Refresh list
        } catch (e: any) {
            alert("Failed to delete user: " + (e.response?.data?.detail || e.message));
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="animate-spin text-purple-400" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-8 text-center text-red-500 bg-red-900/10 rounded-xl border border-red-500/20 m-6 backdrop-blur-sm">
                <AlertTriangle size={48} className="mx-auto mb-4" />
                <h2 className="text-xl font-bold mb-2">Access Denied or Error</h2>
                <p>{error}</p>
                <Button onClick={fetchData} className="mt-4" variant="secondary">Retry</Button>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-[1600px] mx-auto space-y-8 animate-in fade-in duration-500">
            <div className="flex items-center justify-between mb-8">
                <h1 className="text-4xl font-extrabold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent flex items-center gap-3">
                    <Shield className="text-blue-400" size={36} />
                    Admin Dashboard
                </h1>
                <Button onClick={fetchData} variant="secondary" className="gap-2">
                    <RefreshCw size={16} /> Refresh
                </Button>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
                {/* Users Section */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md shadow-xl">
                    <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 text-white/90">
                        <UserIcon className="text-blue-400" /> Users
                        <span className="text-sm font-normal text-white/40 ml-2 bg-white/10 px-2 py-1 rounded-full">{users.length}</span>
                    </h2>

                    <div className="overflow-hidden rounded-xl border border-white/5">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs uppercase bg-black/20 text-gray-400 font-bold tracking-wider">
                                <tr>
                                    <th className="px-6 py-4">User</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4">Role</th>
                                    <th className="px-6 py-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {users.map((user) => (
                                    <tr key={user.id || user._id} className="hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4 font-medium text-white/80">
                                            {user.email}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.is_active
                                                ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                                                : 'bg-red-500/10 text-red-400 border border-red-500/20'
                                                }`}>
                                                {user.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            {user.is_superuser ? (
                                                <span className="inline-flex items-center gap-1 text-purple-400 font-bold text-xs uppercase tracking-wider">
                                                    <Shield size={12} /> Admin
                                                </span>
                                            ) : (
                                                <span className="text-gray-500 text-xs uppercase tracking-wider">User</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right flex justify-end gap-2">
                                            <button
                                                onClick={() => setResetModalUser(user)}
                                                className="p-2 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors"
                                                title="Reset Password"
                                            >
                                                <RefreshCw size={18} />
                                            </button>
                                            <button
                                                onClick={() => setDeleteModalUser(user)}
                                                className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                                                title="Delete User"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Jobs Section */}
                <div className="glass-panel p-6 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-md shadow-xl">
                    <h2 className="text-2xl font-bold mb-6 flex items-center gap-2 text-white/90">
                        <FileAudio className="text-yellow-400" /> Recent Jobs
                        <span className="text-sm font-normal text-white/40 ml-2 bg-white/10 px-2 py-1 rounded-full">{jobs.length}</span>
                    </h2>

                    <div className="overflow-hidden rounded-xl border border-white/5">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs uppercase bg-black/20 text-gray-400 font-bold tracking-wider">
                                <tr>
                                    <th className="px-6 py-4">Job ID</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4">File</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {jobs.map((job) => (
                                    <tr key={job.id || job._id} className="hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4 font-mono text-xs text-gray-500">
                                            {(job.id || job._id).substring(0, 8)}...
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${job.status === 'completed' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                                                job.status === 'failed' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                                                    'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                                                }`}>
                                                {job.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-gray-300 truncate max-w-[200px]" title={job.original_filename}>
                                            {job.original_filename}
                                        </td>
                                    </tr>
                                ))}
                                {jobs.length === 0 && (
                                    <tr>
                                        <td colSpan={3} className="px-6 py-12 text-center text-gray-500 italic">
                                            No jobs found.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* Reset Password Modal */}
            {resetModalUser && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-[#1a1a1a] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl animate-in zoom-in-95 duration-200">
                        <h3 className="text-xl font-bold text-white mb-2">Reset Password</h3>
                        <p className="text-gray-400 mb-6 text-sm">
                            Setting a new password for <span className="text-white font-medium">{resetModalUser.email}</span>.
                            <br /><br />
                            <span className="text-yellow-500 font-bold block bg-yellow-900/20 p-2 rounded border border-yellow-500/20">
                                ⚠️ WARNING: The user will lose access to existing encrypted files unless they have their Recovery Key.
                            </span>
                        </p>
                        <div className="flex gap-2 mb-6">
                            <input
                                type="text"
                                placeholder="New Password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="flex-1 bg-black/30 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 font-mono"
                            />
                            <Button
                                variant="secondary"
                                onClick={() => {
                                    const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*";
                                    const randomPass = Array.from(crypto.getRandomValues(new Uint32Array(12)))
                                        .map(x => chars[x % chars.length])
                                        .join('');
                                    setNewPassword(randomPass);
                                }}
                                title="Generate Random Password"
                            >
                                <RefreshCw size={18} />
                            </Button>
                        </div>
                        <div className="flex justify-end gap-3">
                            <Button variant="secondary" onClick={() => { setResetModalUser(null); setNewPassword(""); }}>
                                Cancel
                            </Button>
                            <Button onClick={handleResetPasswordSubmit} disabled={!newPassword}>
                                Reset Password
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            {/* Delete User Modal */}
            {deleteModalUser && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-[#1a1a1a] border border-red-500/30 rounded-2xl p-6 w-full max-w-md shadow-2xl animate-in zoom-in-95 duration-200">
                        <div className="flex items-center gap-3 text-red-500 mb-4">
                            <AlertTriangle size={24} />
                            <h3 className="text-xl font-bold">Delete User?</h3>
                        </div>
                        <p className="text-gray-300 mb-6 leading-relaxed">
                            Are you sure you want to delete <span className="text-white font-bold">{deleteModalUser.email}</span>?
                            <br /><br />
                            <span className="text-red-400 block">
                                This action cannot be undone. All their jobs, transcripts, and files will be permanently destroyed.
                            </span>
                        </p>
                        <div className="flex justify-end gap-3">
                            <Button variant="secondary" onClick={() => setDeleteModalUser(null)}>
                                Cancel
                            </Button>
                            <button
                                onClick={handleDeleteUserSubmit}
                                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
                            >
                                Yes, Delete User
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
