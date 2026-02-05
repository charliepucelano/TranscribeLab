"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { Button } from '@/components/ui';
import { Plus, Mic, Clock, Calendar, Trash2, RotateCcw } from 'lucide-react';
import styles from './dashboard.module.css';
import { format } from 'date-fns';

interface Job {
    _id: string;
    job_name: string;
    status: string;
    created_at: string;
    duration?: number;
    meeting_type?: string;
    status_message?: string;
    progress?: number;
}

export default function Dashboard() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchJobs();
    }, []);

    useEffect(() => {
        // Polling interval to update progress
        const interval = setInterval(() => {
            const hasActiveJobs = jobs.some(j => j.status === 'processing' || j.status === 'pending');
            if (hasActiveJobs) {
                fetchJobs();
            }
        }, 3000);

        return () => clearInterval(interval);
    }, [jobs]);

    const fetchJobs = async () => {
        try {
            const res = await api.get('/jobs');
            setJobs(res.data);
        } catch (err: any) {
            console.error(err);
            setError('Failed to load jobs. ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    const deleteJob = async (e: React.MouseEvent, id: string) => {
        e.preventDefault();
        e.stopPropagation();
        if (!confirm('Are you sure you want to delete this recording?')) return;
        try {
            await api.delete(`/jobs/${id}`);
            setJobs(prev => prev.filter(j => j._id !== id));
        } catch (err) {
            console.error(err);
            alert('Failed to delete job');
        }
    };

    const retryJob = async (e: React.MouseEvent, id: string) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            // Update UI immediately to show intent
            setJobs(prev => prev.map(j => j._id === id ? { ...j, status: 'pending', status_message: 'Retrying...' } : j));
            await api.post(`/jobs/${id}/retry`);
        } catch (err) {
            console.error(err);
            alert('Failed to retry job');
            fetchJobs(); // Revert to actual state
        }
    };

    return (
        <div>
            <div className={styles.header}>
                <h1 className={styles.title}>My Recordings</h1>
                <Link href="/upload">
                    <Button>
                        <Plus size={18} style={{ marginRight: '0.5rem' }} />
                        New Transcription
                    </Button>
                </Link>
            </div>

            {loading ? (
                <div style={{ padding: '2rem' }}>Loading...</div>
            ) : error ? (
                <div style={{ color: 'red', padding: '2rem' }}>{error}</div>
            ) : jobs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '4rem', color: 'hsl(var(--muted-foreground))' }}>
                    <Mic size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                    <p>No recordings yet. Upload one to get started!</p>
                </div>
            ) : (
                <div className={styles.grid}>
                    {jobs.map((job) => (
                        <Link href={`/jobs/${job._id}`} key={job._id} style={{ textDecoration: 'none' }}>
                            <div className={styles.card}>
                                <div className={styles.cardHeader}>
                                    <div className={styles.icon}>
                                        <Mic size={20} />
                                    </div>
                                    <div style={{ flex: 1 }}></div>
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        {job.status === 'failed' && (
                                            <button
                                                onClick={(e) => retryJob(e, job._id)}
                                                className={styles.deleteButton}
                                                style={{ color: 'hsl(var(--primary))' }}
                                                title="Retry Transcription"
                                            >
                                                <RotateCcw size={16} />
                                            </button>
                                        )}
                                        <button
                                            onClick={(e) => deleteJob(e, job._id)}
                                            className={styles.deleteButton}
                                            title="Delete Recording"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }}>
                                        <span className={`${styles.status} ${job.status === 'completed' ? styles.statusCompleted : job.status === 'failed' ? styles.statusFailed : styles.statusProcessing}`}>
                                            {job.status_message || job.status} {job.status === 'processing' && job.progress ? `(${job.progress}%)` : ''}
                                        </span>
                                        {job.status === 'processing' && (
                                            <div style={{ width: '100%', height: '4px', background: 'hsl(var(--muted))', borderRadius: '2px', overflow: 'hidden' }}>
                                                <div style={{ width: `${job.progress || 0}%`, height: '100%', background: 'hsl(var(--primary))', transition: 'width 0.5s ease' }}></div>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                <h3 className={styles.jobName}>{job.job_name}</h3>

                                <div className={styles.meta}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                        <Calendar size={14} />
                                        <span>{format(new Date(job.created_at), 'MMM d, yyyy')}</span>
                                    </div>
                                    {job.duration && (
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                            <Clock size={14} />
                                            <span>{Math.round(job.duration)}s</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
