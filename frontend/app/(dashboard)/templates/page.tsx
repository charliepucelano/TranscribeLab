"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { Button } from '@/components/ui';
import { Plus, Trash2, Edit } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface Template {
    id: string; // "General Meeting" OR ObjectId string
    name: string;
    description: string;
    system_instruction: string;
    language: string;
    is_custom: boolean;
    can_edit: boolean;
}

export default function TemplatesPage() {
    const [templates, setTemplates] = useState<Template[]>([]);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    useEffect(() => {
        fetchTemplates();
    }, []);

    const fetchTemplates = async () => {
        try {
            const res = await api.get('/templates');
            setTemplates(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure you want to delete this template?")) return;
        try {
            await api.delete(`/templates/${id}`);
            setTemplates(prev => prev.filter(t => t.id !== id));
        } catch (err) {
            console.error("Failed to delete", err);
            alert("Failed to delete template");
        }
    };

    return (
        <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '2rem', fontWeight: 700 }}>Templates</h1>
                <Link href="/templates/new">
                    <Button>
                        <Plus size={16} style={{ marginRight: '0.5rem' }} />
                        New Template
                    </Button>
                </Link>
            </div>

            {loading ? (
                <div>Loading...</div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {templates.map(t => (
                        <div key={t.id} style={{
                            padding: '1.5rem',
                            borderRadius: '8px',
                            border: '1px solid hsl(var(--border))',
                            background: 'hsl(var(--card))',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'start'
                        }}>
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>{t.name}</h3>
                                    {!t.is_custom && (
                                        <span style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem', background: 'hsl(var(--muted))', borderRadius: '4px' }}>Built-in</span>
                                    )}
                                    <span style={{ fontSize: '0.7rem', padding: '0.1rem 0.4rem', border: '1px solid hsl(var(--border))', borderRadius: '4px' }}>
                                        {t.language.toUpperCase()}
                                    </span>
                                </div>
                                <p style={{ color: 'hsl(var(--muted-foreground))', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                                    {t.description || "No description"}
                                </p>
                            </div>

                            {t.can_edit && (
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    <Button variant="ghost" size="small" onClick={() => handleDelete(t.id)} style={{ color: 'hsl(var(--destructive))' }}>
                                        <Trash2 size={16} />
                                    </Button>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
