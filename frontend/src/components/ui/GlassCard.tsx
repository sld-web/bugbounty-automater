import React from 'react';
import { cn } from '@/lib/utils';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'subtle' | 'tactical';
  glow?: 'primary' | 'secondary' | 'tertiary' | 'none';
  onClick?: () => void;
}

export function GlassCard({
  children,
  className,
  variant = 'default',
  glow = 'none',
  onClick
}: GlassCardProps) {
  const variants = {
    default: 'glass-card',
    subtle: 'glass-card-subtle',
    tactical: 'glass-panel',
  };

  const glows = {
    primary: 'shadow-glow-primary',
    secondary: 'shadow-glow-secondary',
    tertiary: 'shadow-glow-tertiary',
    none: '',
  };

  return (
    <div
      className={cn(
        'rounded-lg p-6',
        variants[variant],
        glows[glow],
        onClick && 'cursor-pointer hover:bg-surface-100/50 transition-colors',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
