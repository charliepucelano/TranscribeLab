import React, { useState, useEffect } from 'react';
import { X, Check, type LucideIcon } from 'lucide-react';

interface SpeakerEditModalProps {
    isOpen: boolean;
    onClose: () => void;
    currentSpeaker: string;
    onSave: (newSpeakerName: string, applyToAll: boolean) => void;
}

export function SpeakerEditModal({ isOpen, onClose, currentSpeaker, onSave }: SpeakerEditModalProps) {
    const [name, setName] = useState(currentSpeaker);
    const [applyToAll, setApplyToAll] = useState(true);

    useEffect(() => {
        setName(currentSpeaker);
    }, [currentSpeaker]);

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            backdropFilter: 'blur(4px)'
        }}>
            <div style={{
                backgroundColor: 'hsl(var(--card))',
                padding: '1.5rem',
                borderRadius: '8px',
                width: '100%',
                maxWidth: '400px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                border: '1px solid hsl(var(--border))'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Edit Speaker</h3>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'hsl(var(--muted-foreground))' }}>
                        <X size={20} />
                    </button>
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem' }}>
                        Speaker Name
                    </label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        style={{
                            width: '100%',
                            padding: '0.5rem',
                            borderRadius: '4px',
                            border: '1px solid hsl(var(--border))',
                            backgroundColor: 'hsl(var(--background))',
                            color: 'hsl(var(--foreground))',
                            fontSize: '1rem'
                        }}
                        autoFocus
                    />
                </div>

                <div style={{ marginBottom: '1.5rem' }}>
                    <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem' }}>
                        Apply Changes To:
                    </label>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                            <input
                                type="radio"
                                checked={applyToAll}
                                onChange={() => setApplyToAll(true)}
                                style={{ accentColor: 'hsl(var(--primary))' }}
                            />
                            <span style={{ fontSize: '0.9rem' }}>
                                All segments with <strong>{currentSpeaker}</strong>
                            </span>
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                            <input
                                type="radio"
                                checked={!applyToAll}
                                onChange={() => setApplyToAll(false)}
                                style={{ accentColor: 'hsl(var(--primary))' }}
                            />
                            <span style={{ fontSize: '0.9rem' }}>
                                Only this specific segment
                            </span>
                        </label>
                    </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                    <button
                        onClick={onClose}
                        style={{
                            padding: '0.5rem 1rem',
                            borderRadius: '4px',
                            border: '1px solid hsl(var(--border))',
                            background: 'transparent',
                            cursor: 'pointer',
                            fontSize: '0.9rem',
                            color: 'hsl(var(--foreground))'
                        }}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={() => onSave(name, applyToAll)}
                        style={{
                            padding: '0.5rem 1rem',
                            borderRadius: '4px',
                            border: 'none',
                            background: 'hsl(var(--primary))',
                            color: 'hsl(var(--primary-foreground))',
                            cursor: 'pointer',
                            fontSize: '0.9rem',
                            fontWeight: 500
                        }}
                    >
                        Save Changes
                    </button>
                </div>
            </div>
        </div>
    );
}
