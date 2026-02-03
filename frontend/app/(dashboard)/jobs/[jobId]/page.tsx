"use client";

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui';
import { Play, Pause, Save, Wand2 } from 'lucide-react';
import styles from './editor.module.css';

interface Segment {
    id: number;
    start: number;
    end: number;
    text: string;
    speaker?: string;
}

export default function EditorPage() {
    const params = useParams();
    const jobId = params.jobId as string;

    const [loading, setLoading] = useState(true);
    const [segments, setSegments] = useState<Segment[]>([]);
    const [job, setJob] = useState<any>(null);
    const [summary, setSummary] = useState('');

    useEffect(() => {
        fetchData();
    }, [jobId]);

    const fetchData = async () => {
        try {
            const jobRes = await api.get(`/jobs/${jobId}`);
            setJob(jobRes.data);

            // Fetch Transcript
            if (jobRes.data.status === 'completed') {
                const transRes = await api.get(`/jobs/${jobId}/transcript`);
                // Adapt format: OpenAI verbose_json uses 'segments' array
                const rawSegments = transRes.data.segments || [];
                setSegments(rawSegments.map((s: any, idx: number) => ({
                    id: idx,
                    start: s.start,
                    end: s.end,
                    text: s.text,
                    speaker: 'Speaker' // Default until we parsers diarization labels
                })));

                // Fetch Summary
                try {
                    const sumRes = await api.get(`/jobs/${jobId}/summary`);
                    if (sumRes.data.summary) {
                        setSummary(sumRes.data.summary);
                    }
                } catch (e) {
                    console.error("No summary found or error fetching summary", e);
                }
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleTextChange = (id: number, newText: string) => {
        setSegments(prev => prev.map(s => s.id === id ? { ...s, text: newText } : s));
    };

    const generateSummary = async () => {
        setSummary("Generating summary... This may take a moment.");
        try {
            await api.post(`/jobs/${jobId}/summarize`);
            // Poll for result or just fetch it knowing it's sync in our backend code currently (though backend is async, the await generate_summary waits)
            // Since backend awaits ollama, we can just fetch summary again immediately after.
            const sumRes = await api.get(`/jobs/${jobId}/summary`);
            setSummary(sumRes.data.summary || "Summary generated but returned empty.");
        } catch (err) {
            setSummary("Error generating summary. Please try again.");
            console.error(err);
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    if (loading) return <div className={styles.loading}>Loading Editor...</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>{job?.job_name}</h1>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Button variant="secondary">
                        <Save size={16} style={{ marginRight: '0.5rem' }} />
                        Save Changes
                    </Button>
                </div>
            </div>

            <div className={styles.container}>
                {/* Left: Transcript */}
                <div className={styles.leftPanel}>
                    <div className={styles.panelHeader}>
                        <span className={styles.panelTitle}>Transcript</span>
                    </div>
                    <div className={styles.scrollArea}>
                        {segments.map((seg) => (
                            <div key={seg.id} className={styles.segment}>
                                <div className={styles.timestamp}>
                                    {formatTime(seg.start)} - {formatTime(seg.end)}
                                </div>
                                <div className={styles.content}>
                                    <div className={styles.speaker}>{seg.speaker}</div>
                                    <textarea
                                        className={styles.textEditor}
                                        value={seg.text}
                                        onChange={(e) => handleTextChange(seg.id, e.target.value)}
                                        rows={Math.max(2, Math.ceil(seg.text.length / 80))}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right: Summary */}
                <div className={styles.rightPanel}>
                    <div className={styles.panelHeader}>
                        <span className={styles.panelTitle}>AI Summary</span>
                        <Button size="small" variant="ghost" onClick={generateSummary} title="Generate Summary">
                            <Wand2 size={16} />
                        </Button>
                    </div>
                    <div className={styles.scrollArea}>
                        <div className={styles.summaryContent}>
                            {summary || "Click Generate to create a summary."}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
