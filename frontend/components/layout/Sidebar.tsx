"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, FileAudio, Settings, LogOut, Menu, FileText } from 'lucide-react';
import styles from './sidebar.module.css';

const navItems = [
    { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { label: 'Jobs', href: '/jobs', icon: FileAudio },
    { label: 'Templates', href: '/templates', icon: FileText },
    { label: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();
    const [isOpen, setIsOpen] = React.useState(false);

    // Close sidebar on route change (mobile)
    React.useEffect(() => {
        setIsOpen(false);
    }, [pathname]);

    return (
        <>
            {/* Mobile Toggle Button */}
            <button
                className={styles.toggleButton}
                onClick={() => setIsOpen(!isOpen)}
                aria-label="Toggle Menu"
            >
                <Menu size={24} />
            </button>

            {/* Overlay for mobile */}
            <div
                className={`${styles.overlay} ${isOpen ? styles.visible : ''}`}
                onClick={() => setIsOpen(false)}
            />

            <aside className={`${styles.sidebar} ${isOpen ? styles.open : ''}`}>
                <div className={styles.header}>
                    <span className={styles.logo}>TranscribeLab</span>
                </div>

                <nav className={styles.nav}>
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname === item.href;

                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`${styles.item} ${isActive ? styles.active : ''}`}
                            >
                                <Icon size={20} />
                                <span>{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className={styles.footer}>
                    <Link href="/auth/login" className={styles.item} onClick={() => {
                        localStorage.removeItem('token');
                        setIsOpen(false);
                    }}>
                        <LogOut size={20} />
                        <span>Sign Out</span>
                    </Link>
                </div>
            </aside>
        </>
    );
}
