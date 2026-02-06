"use client";

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui';
import { Play, Pause, Save, Wand2, Users, Scissors, Edit } from 'lucide-react';
import { SpeakerEditModal } from '@/components/SpeakerEditModal';
import styles from './editor.module.css';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Segment {
    id: number;
    start: number;
    end: number;
    text: string;
    speaker?: string;
}

interface Template {
    name: string;
    description: string;
}

export default function EditorPage() {
    const params = useParams();
    const jobId = params.jobId as string;

    const [loading, setLoading] = useState(true);
    const [segments, setSegments] = useState<Segment[]>([]);
    const [job, setJob] = useState<any>(null);
    const [summary, setSummary] = useState('');

    // Template State
    const [templates, setTemplates] = useState<Template[]>([]);
    const [selectedTemplate, setSelectedTemplate] = useState<string>('');


    // Smart Edit Modal State
    const [editSpeakerModal, setEditSpeakerModal] = useState<{ isOpen: boolean, speaker: string, segmentId: number } | null>(null);

    useEffect(() => {
        fetchTemplates();
        fetchData();
    }, [jobId]);

    const fetchTemplates = async () => {
        try {
            const res = await api.get('/templates');
            setTemplates(res.data);
            if (res.data.length > 0) {
                // Default to "General Meeting" if exists, else first one
                const general = res.data.find((t: Template) => t.name === "General Meeting");
                setSelectedTemplate(general ? general.name : res.data[0].name);
            }
        } catch (err) {
            console.error("Failed to load templates", err);
        }
    };

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
                    speaker: s.speaker || 'Speaker' // Use diarized speaker if available
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

    // SSE for Real-time Progress
    useEffect(() => {
        let eventSource: EventSource | null = null;

        // Only connect if job is valid and processing
        const shouldConnect = job?.status === 'processing' || job?.status === 'pending' || (job?.status_message && job.status_message.includes('Diariz'));

        if (shouldConnect) {
            const token = localStorage.getItem('token');
            // Assuming BACKEND_URL is available via env or we construct it. 
            // Since api.ts uses axios baseURL, we need the raw URL.
            // Hardcoding for MVP or extracting from env if possible.
            // Window.location logic is safer if proxying, but we are separate ports.
            const backendUrl = process.env.NEXT_PUBLIC_API_URL || '/api';
            const url = `${backendUrl}/jobs/${jobId}/events?token=${token}`;

            eventSource = new EventSource(url);

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    // data: {status, progress, message, timestamp}

                    if (data.status === 'completed' && job?.status !== 'completed') {
                        // Reload full data to get transcript
                        fetchData();
                        eventSource?.close();
                    } else if (data.status === 'failed') {
                        setJob((prev: any) => ({ ...prev, status: 'failed', status_message: data.message }));
                        eventSource?.close();
                    } else {
                        // Update job state locally for smooth progress
                        setJob((prev: any) => ({
                            ...prev,
                            status: data.status,
                            progress: data.progress,
                            status_message: data.message
                        }));
                    }
                } catch (e) {
                    console.error("SSE Parse Error", e);
                }
            };

            eventSource.onerror = (err) => {
                console.error("SSE Connection Error", err);
                eventSource?.close();
                // Fallback to polling implementation inside fetchData if SSE fails?
                // For now, retry logic is handled by browser EventSource (auto reconnects), 
                // but if token invalid, it might loop.
            };
        }

        return () => {
            if (eventSource) {
                eventSource.close();
            }
        };
    }, [jobId, job?.status]); // Re-run if status changes (e.g. from pending to processing)

    // Initial Fetch (One-off)
    useEffect(() => {
        fetchData();
    }, [jobId]);

    const handleTextChange = (id: number, newText: string) => {
        setSegments(prev => prev.map(s => s.id === id ? { ...s, text: newText } : s));
    };

    const openSpeakerEdit = (currentSpeaker: string, segmentId: number) => {
        setEditSpeakerModal({ isOpen: true, speaker: currentSpeaker, segmentId });
    };

    const saveSpeakerEdit = (newSpeaker: string, applyToAll: boolean) => {
        if (!editSpeakerModal) return;

        const oldSpeakerName = editSpeakerModal.speaker;
        const targetId = editSpeakerModal.segmentId;

        if (applyToAll) {
            setSegments(prev => prev.map(s =>
                s.speaker === oldSpeakerName ? { ...s, speaker: newSpeaker } : s
            ));
        } else {
            setSegments(prev => prev.map(s =>
                s.id === targetId ? { ...s, speaker: newSpeaker } : s
            ));
        }
        setEditSpeakerModal(null);
    };

    const handleSave = async () => {
        try {
            await api.put(`/jobs/${jobId}/transcript`, { segments });
            alert("Transcript saved successfully!");
        } catch (err) {
            console.error(err);
            alert("Failed to save transcript.");
        }
    };

    const handleRediarize = async () => {
        if (!confirm("This will attempt to run AI Diarization again and OVERWRITE current speaker labels. Continue?")) return;
        try {
            await api.post(`/jobs/${jobId}/diarize`);
            alert("Diarization started. Please wait a moment for updates.");
            // Force status reload
            fetchData();
        } catch (err) {
            console.error(err);
            alert("Failed to start diarization.");
        }
    };

    const generateSummary = async () => {
        setSummary("Generating summary... This may take a moment.");
        try {
            await api.post(`/jobs/${jobId}/summarize`, { template_name: selectedTemplate });
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

    const handleSplit = (segId: number, cursorIndex: number) => {
        setSegments(prev => {
            const segIndex = prev.findIndex(s => s.id === segId);
            if (segIndex === -1) return prev;

            const original = prev[segIndex];

            // Calculate split time (Linear Interpolation as fallback)
            // TODO: Use word-level timestamps if available for better precision
            const duration = original.end - original.start;
            const progress = cursorIndex / original.text.length;
            const splitTime = original.start + (duration * progress);

            // Create two new segments
            const firstHalf = {
                ...original,
                end: splitTime,
                text: original.text.substring(0, cursorIndex).trim()
            };

            const secondHalf = {
                ...original,
                id: Math.max(...prev.map(s => s.id)) + 1, // New ID
                start: splitTime,
                text: original.text.substring(cursorIndex).trim()
            };

            // Insert secondHalf after firstHalf
            const newSegments = [...prev];
            newSegments[segIndex] = firstHalf;
            newSegments.splice(segIndex + 1, 0, secondHalf);

            return newSegments;
        });
    };

    if (loading) return <div className={styles.loading}>Loading Editor...</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>{job?.job_name}</h1>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Button variant="ghost" onClick={handleRediarize} title="Retry AI Speaker Detection">
                        <Users size={16} style={{ marginRight: '0.5rem' }} />
                        Rediarize
                    </Button>
                    <Button variant="secondary" onClick={handleSave}>
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
                        {job?.status && (
                            <span className={job.status === 'completed' ? styles.statusCompleted : styles.statusProcessing} style={{ fontSize: '0.8rem', marginLeft: '1rem', padding: '0.2rem 0.5rem', borderRadius: '4px' }}>
                                {job.status.toUpperCase()}
                            </span>
                        )}
                    </div>
                    <div className={styles.scrollArea}>
                        {(job?.status === 'processing' || job?.status === 'pending' || (job?.status !== 'completed' && job?.status_message && job.status_message.includes('Diariz'))) ? (
                            <div className={styles.loadingState}>
                                <div className={styles.spinner}></div>
                                <p>{job?.status_message || "Transcription in progress..."}</p>
                                {job?.progress !== undefined && (
                                    <div style={{ width: '300px', height: '6px', background: 'hsl(var(--muted))', borderRadius: '3px', overflow: 'hidden', marginTop: '1rem' }}>
                                        <div style={{ width: `${job.progress}%`, height: '100%', background: 'hsl(var(--primary))', transition: 'width 0.5s ease' }}></div>
                                    </div>
                                )}
                                <p style={{ fontSize: '0.9rem', color: 'hsl(var(--muted-foreground))', marginTop: '0.5rem' }}>
                                    {job?.progress ? `${job.progress}% Complete` : 'This may take a few minutes depending on file size.'}
                                </p>
                            </div>
                        ) : job?.status === 'failed' ? (
                            <div className={styles.errorState}>
                                <p>Transcription Failed.</p>
                                <p style={{ fontSize: '0.8rem', opacity: 0.7 }}>{job.status_message}</p>
                            </div>
                        ) : segments.length > 0 ? (
                            segments.map((seg) => (
                                <div key={seg.id} className={styles.segment}>
                                    <div className={styles.timestamp}>
                                        {formatTime(seg.start)} - {formatTime(seg.end)}
                                    </div>
                                    <div className={styles.content}>
                                        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                            <div
                                                onClick={() => openSpeakerEdit(seg.speaker || "Speaker", seg.id)}
                                                className={styles.speakerLabel}
                                                style={{
                                                    cursor: 'pointer',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.5rem',
                                                    fontWeight: 600,
                                                    color: 'hsl(var(--primary))',
                                                    padding: '0.2rem 0.5rem',
                                                    borderRadius: '4px',
                                                    backgroundColor: 'hsl(var(--muted)/0.3)',
                                                    border: '1px solid transparent'
                                                }}
                                                onMouseEnter={(e) => e.currentTarget.style.borderColor = 'hsl(var(--primary)/0.5)'}
                                                onMouseLeave={(e) => e.currentTarget.style.borderColor = 'transparent'}
                                                title="Click to rename speaker"
                                            >
                                                {seg.speaker || "Speaker"}
                                                <Edit size={12} style={{ opacity: 0.6 }} />
                                            </div>

                                            <Button
                                                variant="ghost"
                                                size="small"
                                                onClick={() => {
                                                    // Find the textarea for this segment
                                                    // We use a query selector because we don't have refs for dynamic list easily without refactoring
                                                    const textarea = document.getElementById(`textarea-${seg.id}`) as HTMLTextAreaElement;
                                                    if (textarea) {
                                                        const cursor = textarea.selectionStart;
                                                        if (cursor > 0 && cursor < seg.text.length) {
                                                            handleSplit(seg.id, cursor);
                                                        } else {
                                                            alert("Place cursor in text where you want to split.");
                                                            textarea.focus();
                                                        }
                                                    }
                                                }}
                                                title="Split segment at cursor position"
                                            >
                                                <Scissors size={14} />
                                            </Button>
                                        </div>
                                        <textarea
                                            id={`textarea-${seg.id}`}
                                            className={styles.textEditor}
                                            value={seg.text}
                                            onChange={(e) => handleTextChange(seg.id, e.target.value)}
                                            rows={Math.max(2, Math.ceil(seg.text.length / 80))}
                                            placeholder="Transcript text..."
                                        />
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className={styles.emptyState}>No transcript available.</div>
                        )}
                    </div>
                </div>

                {/* Right: Summary */}
                <div className={styles.rightPanel}>
                    <div className={styles.panelHeader}>
                        <span className={styles.panelTitle}>AI Summary</span>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <select
                                value={selectedTemplate}
                                onChange={(e) => setSelectedTemplate(e.target.value)}
                                style={{
                                    background: 'transparent',
                                    color: 'hsl(var(--foreground))',
                                    border: '1px solid hsl(var(--border))',
                                    borderRadius: '4px',
                                    padding: '0.2rem 0.5rem',
                                    fontSize: '0.8rem',
                                    outline: 'none'
                                }}
                            >
                                {templates.map(t => (
                                    <option key={t.name} value={t.name} style={{ background: 'hsl(var(--card))' }}>
                                        {t.name}
                                    </option>
                                ))}
                            </select>
                            <Button size="small" variant="ghost" onClick={generateSummary} title="Generate Summary">
                                <Wand2 size={16} />
                            </Button>
                        </div>
                    </div>
                    <div className={styles.scrollArea}>
                        <div className={styles.summaryContent}>
                            {summary ? (
                                <div className={styles.markdown}>
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {summary}
                                    </ReactMarkdown>
                                </div>
                            ) : (
                                "Click Generate to create a summary."
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Modal */}
            <SpeakerEditModal
                isOpen={!!editSpeakerModal}
                onClose={() => setEditSpeakerModal(null)}
                currentSpeaker={editSpeakerModal?.speaker || ''}
                onSave={saveSpeakerEdit}
            />
        </div>
    );
}
