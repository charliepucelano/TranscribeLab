"use client";

import React, { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button, Input } from '@/components/ui';
import { UploadCloud, FileAudio, X } from 'lucide-react';
import styles from './upload.module.css';

export default function UploadPage() {
    const router = useRouter();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [file, setFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

    // Form Fields
    const [jobName, setJobName] = useState('');
    const [language, setLanguage] = useState('en');
    const [numSpeakers, setNumSpeakers] = useState('');
    const [meetingType, setMeetingType] = useState('General Meeting');

    const handleDrag = (e: React.DragEvent) => {
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
        if (!file.type.startsWith('audio/')) {
            // Allow common extensions if type missing
            const ext = file.name.split('.').pop()?.toLowerCase();
            if (!['mp3', 'wav', 'm4a', 'flac', 'ogg'].includes(ext || '')) {
                setError('Please upload a valid audio file (mp3, wav, m4a, flac, ogg)');
                return;
            }
        }
        setError('');
        setFile(file);
        if (!jobName) {
            setJobName(file.name.split('.')[0]);
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
        formData.append('language', language);
        if (numSpeakers) formData.append('num_speakers', numSpeakers);
        formData.append('meeting_type', meetingType);
        if (jobName) formData.append('job_name', jobName);

        try {
            await api.post('/jobs/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 100));
                    setUploadProgress(percentCompleted);
                }
            });

            router.push('/dashboard');
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || 'Upload failed. Please try again.');
            setUploading(false);
        }
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Upload Recording</h1>

            <form onSubmit={handleUpload} className={styles.form}>
                {error && <div className={styles.error}>{error}</div>}

                {/* Dropzone */}
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
                            Drag & drop your audio file here or <span className={styles.dropzoneHighlight}>browse</span>
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

                {/* Progress Bar */}
                {uploading && (
                    <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                            <span>Uploading...</span>
                            <span>{uploadProgress}%</span>
                        </div>
                        <div className={styles.progressContainer}>
                            <div className={styles.progressBar} style={{ width: `${uploadProgress}%` }}></div>
                        </div>
                    </div>
                )}

                <div className={styles.formGrid}>
                    <Input
                        label="Job Name"
                        value={jobName}
                        onChange={(e) => setJobName(e.target.value)}
                        disabled={uploading}
                    />

                    <div className="input-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <label style={{ fontSize: '0.875rem', fontWeight: 500, color: 'hsl(var(--foreground))' }}>Meeting Type</label>
                        <select
                            className={styles.select}
                            value={meetingType}
                            onChange={(e) => setMeetingType(e.target.value)}
                            disabled={uploading}
                        >
                            <option value="General Meeting">General Meeting</option>
                            <option value="Interview">Interview</option>
                            <option value="Team Standup">Team Standup</option>
                            <option value="Client Call">Client Call</option>
                            <option value="Sales Call">Sales Call</option>
                            <option value="Brainstorming Session">Brainstorming Session</option>
                        </select>
                    </div>

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
                </div>

                <Button type="submit" fullWidth disabled={!file || uploading}>
                    {uploading ? 'Processing...' : 'Start Transcription'}
                </Button>
            </form>
        </div>
    );
}
