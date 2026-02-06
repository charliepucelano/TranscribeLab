"use client";

import React, { useState } from 'react';
import api from '@/lib/api';
import { Button, Input } from '@/components/ui';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function NewTemplatePage() {
    const router = useRouter();
    const [formData, setFormData] = useState({
        name: '',
        language: 'en',
        description: '',
        system_instruction: ''
    });
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await api.post('/templates', formData);
            router.push('/templates');
        } catch (err) {
            console.error("Failed to create template", err);
            alert("Failed to create template. Check console for details.");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
            <Link href="/templates" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'hsl(var(--muted-foreground))', marginBottom: '1rem' }}>
                <ArrowLeft size={16} />
                Back to Templates
            </Link>

            <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginBottom: '2rem' }}>Create New Template</h1>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Template Name</label>
                    <Input
                        required
                        placeholder="e.g. Sales Call, Daily Standup"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    />
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Language</label>
                    <select
                        value={formData.language}
                        onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                        style={{
                            width: '100%',
                            padding: '0.5rem',
                            borderRadius: 'var(--radius)',
                            border: '1px solid hsl(var(--border))',
                            background: 'hsl(var(--background))',
                            color: 'hsl(var(--foreground))'
                        }}
                    >
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                    </select>
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>Description (Optional)</label>
                    <Input
                        placeholder="Briefly describe what this template is for"
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    />
                </div>

                <div>
                    <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>System Instruction (Prompt)</label>
                    <p style={{ fontSize: '0.8rem', color: 'hsl(var(--muted-foreground))', marginBottom: '0.5rem' }}>
                        This tells the AI how to summarize. Use Markdown for structure.
                    </p>
                    <textarea
                        required
                        rows={10}
                        placeholder={`Summarize the meeting as follows:\n\n## Key Points\n- Point 1\n- Point 2\n\n## Decisions\n...`}
                        value={formData.system_instruction}
                        onChange={(e) => setFormData({ ...formData, system_instruction: e.target.value })}
                        style={{
                            width: '100%',
                            padding: '0.75rem',
                            borderRadius: 'var(--radius)',
                            border: '1px solid hsl(var(--border))',
                            background: 'hsl(var(--background))',
                            color: 'hsl(var(--foreground))',
                            fontFamily: 'monospace',
                            resize: 'vertical'
                        }}
                    />
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                    <Link href="/templates">
                        <Button variant="ghost" type="button">Cancel</Button>
                    </Link>
                    <Button type="submit" disabled={submitting}>
                        {submitting ? 'Creating...' : 'Create Template'}
                    </Button>
                </div>
            </form>
        </div>
    );
}
