"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { Button } from '@/components/ui';
import { Plus, Mic, Clock, Calendar } from 'lucide-react';
import styles from './dashboard.module.css';
import { format } from 'date-fns';

interface Job {
    _id: string;
    job_name: string;
    status: string;
    created_at: string;
    duration?: number;
    meeting_type?: string;
}

export default function Dashboard() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchJobs();
    }, []);

    const fetchJobs = async () => {
        try {
            const res = await api.get('/jobs/');
            setJobs(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
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
                <div>Loading...</div>
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
                                    <span className={`${styles.status} ${job.status === 'completed' ? styles.statusCompleted : styles.statusProcessing}`}>
                                        {job.status}
                                    </span>
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
