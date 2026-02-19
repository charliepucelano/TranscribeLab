import React from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import styles from './layout.module.css';

import { ForcePasswordCheck } from '@/components/auth/ForcePasswordCheck';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <ForcePasswordCheck>
            <div className={styles.container}>
                <Sidebar />
                <main className={styles.main}>
                    {children}
                </main>
            </div>
        </ForcePasswordCheck>
    );
}
