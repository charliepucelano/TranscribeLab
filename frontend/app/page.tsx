
import Link from 'next/link';
import styles from './landing.module.css';

export default function Home() {
  return (
    <div className={styles.container}>
      <div className={styles.hero}>
        <h1 className={styles.title}>TranscribeLab</h1>
        <p className={styles.subtitle}>
          Secure, AI-powered meeting transcription and summarization.
          Your data never leaves your device.
        </p>

        <div className={styles.buttons}>
          <Link href="/auth/login" className={`${styles.button} ${styles.primary}`}>
            Login
          </Link>
          <Link href="/auth/register" className={`${styles.button} ${styles.secondary}`}>
            Create Account
          </Link>
        </div>
      </div>
    </div>
  );
}
