import React from 'react';
import styles from './button.module.css';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'outline';
    size?: 'default' | 'small' | 'large' | 'icon';
    fullWidth?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = 'primary', size = 'default', fullWidth, ...props }, ref) => {
        const classes = [
            styles.button,
            styles[variant],
            styles[size],
            fullWidth ? styles.fullWidth : '',
            className
        ].filter(Boolean).join(' ');

        return <button ref={ref} className={classes} {...props} />;
    }
);

Button.displayName = 'Button';
