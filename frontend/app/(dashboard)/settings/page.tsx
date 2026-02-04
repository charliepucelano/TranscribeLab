"use client";

import React from 'react';
import styles from './settings.module.css';

export default function SettingsPage() {
    const [inviteLink, setInviteLink] = React.useState('');
    const [loadingInvite, setLoadingInvite] = React.useState(false);

    const generateInvite = async () => {
        try {
            setLoadingInvite(true);
            // Dynamic import to avoid SSR issues if api differs, but standard import is fine
            const { default: api } = await import('@/lib/api');
            const res = await api.post('/auth/invite');
            setInviteLink(res.data.invitation_link);
        } catch (e) {
            console.error("Failed to generate invite", e);
        } finally {
            setLoadingInvite(false);
        }
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Settings</h1>

            <section className={styles.section}>
                <h2>Invite Users</h2>
                <p>Generate a link to invite colleagues to TranscribeLab.</p>

                {!inviteLink ? (
                    <button
                        onClick={generateInvite}
                        disabled={loadingInvite}
                        style={{
                            marginTop: '1rem',
                            padding: '0.5rem 1rem',
                            background: 'white',
                            color: 'black',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        {loadingInvite ? 'Generating...' : 'Generate Invite Link'}
                    </button>
                ) : (
                    <div style={{ marginTop: '1rem', background: 'rgba(255,255,255,0.05)', padding: '1rem', borderRadius: '4px' }}>
                        <p style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#aaa' }}>Share this link:</p>
                        <code style={{ display: 'block', wordBreak: 'break-all', color: '#4ade80' }}>
                            {inviteLink}
                        </code>
                    </div>
                )}
            </section>

            <section className={styles.section}>
                <h2>Account Settings</h2>
                <p>Manage your account preferences and security.</p>
                {/* Future: Add password change, email update, etc. */}
            </section>

            <section className={styles.section}>
                <h2>Application Preferences</h2>
                <p>Customize your experience.</p>
                {/* Future: Theme toggle, language preference, etc. */}
            </section>
        </div>
    );
}
