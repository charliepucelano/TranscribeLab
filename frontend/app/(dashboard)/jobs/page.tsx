"use client";

import React from 'react';
import styles from './jobs.module.css';

export default function JobsPage() {
    return (
        <div className={styles.container}>
            <h1 className={styles.title}>All Jobs</h1>
            <p className={styles.description}>
                View and manage your transcription jobs here.
            </p>
            {/* Future: Reuse Job List component here */}
            <div className={styles.placeholder}>
                Job listing coming soon. Please use the Dashboard for now.
            </div>
        </div>
    );
}
