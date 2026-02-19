
"use client";

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import api from '@/lib/api';

export function ForcePasswordCheck({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [checking, setChecking] = useState(true);

    useEffect(() => {
        // Skip check if on auth pages
        if (pathname.startsWith('/auth/')) {
            setChecking(false);
            return;
        }

        const checkUserStatus = async () => {
            try {
                if (!localStorage.getItem('token')) {
                    setChecking(false);
                    return;
                }

                const res = await api.get('/auth/me');
                if (res.data?.force_password_change) {
                    router.push('/auth/change-password');
                    // Don't set checking false, keep blocking until redirect happens
                } else {
                    setChecking(false);
                }
            } catch (error) {
                setChecking(false);
            }
        };

        checkUserStatus();
    }, [pathname, router]);

    if (checking) {
        // Render a simple full-screen loader or nothing
        return <div className="fixed inset-0 bg-[#0a0a0a] z-[100]" />;
    }

    return <>{children}</>;
}
