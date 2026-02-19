"use client";

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button, Input } from '@/components/ui';
import { UploadCloud, FileAudio, X, ChevronDown, ChevronRight } from 'lucide-react';
import styles from './upload.module.css';

export default function UploadPage() {
    const router = useRouter();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [file, setFile] = useState<File | null>(null);
    const [transcriptFile, setTranscriptFile] = useState<File | null>(null); // For Alignment
    const [dragActive, setDragActive] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

    // Advanced Settings State
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [vadOnset, setVadOnset] = useState(0.4); // Default 0.4
    const [minSilence, setMinSilence] = useState(250); // Default 250ms
    const [minSpeakers, setMinSpeakers] = useState('');
    const [maxSpeakers, setMaxSpeakers] = useState('');

    // Form Fields
    const [jobName, setJobName] = useState('');
    const [language, setLanguage] = useState('en');
    const [numSpeakers, setNumSpeakers] = useState(''); // Legacy/Simple

    const handleDrag = (e: React.DragEvent) => {
        // ... existing handleDrag ...
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            validateAndSetFile(e.dataTransfer.files[0]);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0]);
        }
    };

    const validateAndSetFile = (file: File) => {
        // Validate type
        const audioExtensions = ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'webm', 'aac'];
        if (!file.type.startsWith('audio/')) {
            // Allow common extensions if type missing
            const ext = file.name.split('.').pop()?.toLowerCase();
            if (!audioExtensions.includes(ext || '')) {
                setError('Please upload a valid audio file (mp3, wav, m4a, flac, ogg)');
                return;
            }
        }
        setError('');
        setFile(file);

        // Auto-generate job name if not already set by user
        if (!jobName.trim()) {
            const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "");
            setJobName(nameWithoutExt);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setUploading(true);
        setUploadProgress(0);
        setError('');

        const formData = new FormData();
        formData.append('file', file);
        if (transcriptFile) {
            formData.append('transcript_file', transcriptFile);
        }
        formData.append('language', language);

        // Logic: specific min/max take precedence. 
        // If not set, check numSpeakers (simple mode).
        let finalMin = minSpeakers;
        let finalMax = maxSpeakers;

        if (!finalMin && !finalMax && numSpeakers) {
            finalMin = numSpeakers;
            finalMax = numSpeakers;
        }

        if (numSpeakers) formData.append('num_speakers', numSpeakers); // Keep for legacy

        if (jobName) formData.append('job_name', jobName);

        // Construct Config
        const config = {
            vad_onset: vadOnset,
            min_silence_duration_ms: minSilence,
            min_speakers: finalMin ? parseInt(finalMin) : undefined, // Explicit undefined if empty
            max_speakers: finalMax ? parseInt(finalMax) : undefined
        };
        formData.append('config', JSON.stringify(config));

        try {
            // MATCHED: Restore /jobs/upload for explicit routing
            await api.post('/jobs/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 100));
                    setUploadProgress(percentCompleted);
                }
            });

            router.push('/dashboard');
        } catch (err: any) {
            console.error("Upload failed", err);
            setError(err.response?.data?.detail || 'Upload failed. Please check server logs.');
            setUploading(false);
        }
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Upload Recording</h1>

            <form onSubmit={handleUpload} className={styles.form}>
                {error && <div className={styles.error}>{error}</div>}

                {/* STEP 1: AUDIO */}
                <div style={{ marginBottom: '1.5rem' }}>
                    <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'hsl(var(--primary))', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ background: 'hsl(var(--primary))', color: 'white', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>1</span>
                        Audio Recording
                    </h2>
                    {!file ? (
                        <div
                            className={`${styles.dropzone} ${dragActive ? styles.dropzoneActive : ''}`}
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <UploadCloud size={48} color={dragActive ? "hsl(var(--primary))" : "hsl(var(--muted-foreground))"} />
                            <p className={styles.dropzoneText}>
                                Drag & drop your **audio file** here or <span className={styles.dropzoneHighlight}>browse</span>
                            </p>
                            <p className={styles.fileSize}>Supports MP3, WAV, M4A, FLAC, OGG</p>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="audio/*,.m4a"
                                onChange={handleChange}
                                style={{ display: 'none' }}
                            />
                        </div>
                    ) : (
                        <div className={styles.fileInfo}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <FileAudio size={24} color="hsl(var(--primary))" />
                                <div>
                                    <p className={styles.fileName}>{file.name}</p>
                                    <p className={styles.fileSize}>{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setFile(null)}
                                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'hsl(var(--muted-foreground))' }}
                                disabled={uploading}
                            >
                                <X size={20} />
                            </button>
                        </div>
                    )}
                </div>

                {/* STEP 2: DETAILS */}
                <div style={{ marginBottom: '1rem' }}>
                    <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'hsl(var(--primary))', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ background: 'hsl(var(--primary))', color: 'white', width: '24px', height: '24px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem' }}>2</span>
                        Processing Details
                    </h2>

                    <div className={styles.formGrid}>
                        <Input
                            label="Job Name"
                            value={jobName}
                            onChange={(e) => setJobName(e.target.value)}
                            disabled={uploading}
                        />



                        <div className="input-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'hsl(var(--foreground))' }}>Language</label>
                            <select
                                className={styles.select}
                                value={language}
                                onChange={(e) => setLanguage(e.target.value)}
                                disabled={uploading}
                            >
                                <option value="en">English (en)</option>
                                <option value="es">Spanish (es)</option>
                            </select>
                        </div>

                        <Input
                            label="Speakers (Optional)"
                            type="number"
                            min="1"
                            placeholder="Auto-detect"
                            value={numSpeakers}
                            onChange={(e) => setNumSpeakers(e.target.value)}
                            disabled={uploading}
                        />

                        {/* Alignment Mode / Transcript Upload */}
                        <div className="input-wrapper" style={{ gridColumn: '1 / -1', marginTop: '0.5rem', padding: '0.75rem', borderRadius: 'var(--radius)', border: '1px dashed hsl(var(--border))', background: 'hsl(var(--muted)/0.3)' }}>
                            <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'hsl(var(--foreground))', marginBottom: '0.25rem', display: 'block' }}>
                                HiDock Mode: Use Existing Transcript (Optional)
                            </label>
                            <p style={{ fontSize: '0.75rem', color: 'hsl(var(--muted-foreground))', marginBottom: '0.5rem' }}>
                                Upload .srt (recommended) or .txt to skip transcription and just Align & Diarize.
                            </p>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                <input
                                    type="file"
                                    accept=".txt,.srt"
                                    onChange={(e) => setTranscriptFile(e.target.files ? e.target.files[0] : null)}
                                    disabled={uploading}
                                    style={{ fontSize: '0.8rem' }}
                                />
                                {transcriptFile && (
                                    <button
                                        type="button"
                                        onClick={() => setTranscriptFile(null)}
                                        style={{ color: 'hsl(var(--destructive))', background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.8rem' }}
                                    >
                                        Remove
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Advanced Settings Accordion */}
                        <div style={{ gridColumn: '1 / -1', marginTop: '0.5rem' }}>
                            <button
                                type="button"
                                onClick={() => setShowAdvanced(!showAdvanced)}
                                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'none', border: 'none', fontSize: '0.85rem', fontWeight: 600, color: 'hsl(var(--primary))', cursor: 'pointer' }}
                            >
                                {showAdvanced ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                                Advanced Diarization Settings
                            </button>

                            {showAdvanced && (
                                <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', padding: '1rem', background: 'hsl(var(--muted)/0.2)', borderRadius: '8px' }}>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                        <label style={{ fontSize: '0.8rem', fontWeight: 500 }}>VAD Onset Threshold ({vadOnset})</label>
                                        <input
                                            type="range"
                                            min="0.1"
                                            max="0.9"
                                            step="0.05"
                                            value={vadOnset}
                                            onChange={(e) => setVadOnset(parseFloat(e.target.value))}
                                            className={styles.rangeInput}
                                        />
                                        <p style={{ fontSize: '0.7rem', color: 'hsl(var(--muted-foreground))' }}>Higher = Less sensitive to noise (0.4-0.6 rec).</p>
                                    </div>

                                    <Input
                                        label="Min Silence (ms)"
                                        type="number"
                                        value={minSilence}
                                        onChange={(e) => setMinSilence(parseInt(e.target.value))}
                                        placeholder="250"
                                    />

                                    <Input
                                        label="Min Speakers"
                                        type="number"
                                        value={minSpeakers}
                                        onChange={(e) => setMinSpeakers(e.target.value)}
                                        placeholder="Auto"
                                    />

                                    <Input
                                        label="Max Speakers"
                                        type="number"
                                        value={maxSpeakers}
                                        onChange={(e) => setMaxSpeakers(e.target.value)}
                                        placeholder="Auto"
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Progress Bar */}
                {uploading && (
                    <div style={{ marginBottom: '1.5rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                            <span>Uploading...</span>
                            <span>{uploadProgress}%</span>
                        </div>
                        <div className={styles.progressContainer}>
                            <div className={styles.progressBar} style={{ width: `${uploadProgress}%` }}></div>
                        </div>
                    </div>
                )}

                <Button type="submit" fullWidth disabled={!file || uploading}>
                    {uploading ? 'Processing...' : 'Start Transcription'}
                </Button>
            </form>
        </div>
    );
}
