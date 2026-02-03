import React from 'react';
import { Sidebar } from '@/components/layout/Sidebar';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div style={{ display: 'flex' }}>
            <Sidebar />
            <main style={{
                flex: 1,
                marginLeft: '280px',
                minHeight: '100vh',
                backgroundColor: 'hsl(var(--background))',
                padding: '2rem'
            }}>
                {children}
            </main>
        </div>
    );
}
