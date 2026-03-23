import React from 'react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
  color?: 'primary' | 'secondary' | 'tertiary' | 'error';
  className?: string;
}

const colorMap = {
  primary: 'text-primary',
  secondary: 'text-secondary',
  tertiary: 'text-tertiary',
  error: 'text-error',
};

export function MetricCard({
  label,
  value,
  icon,
  trend,
  color = 'primary',
  className
}: MetricCardProps) {
  return (
    <div className={cn('glass-card p-6', className)}>
      <div className="flex items-start justify-between mb-4">
        <span className="metric-label">{label}</span>
        {icon && <span className="text-secondary">{icon}</span>}
      </div>
      <div className="flex items-end gap-3">
        <span className={cn('metric-value', colorMap[color])}>
          {value}
        </span>
        {trend && (
          <span
            className={cn(
              'text-xs font-mono',
              trend.direction === 'up' ? 'text-tertiary' : 'text-error'
            )}
          >
            {trend.direction === 'up' ? '↑' : '↓'} {Math.abs(trend.value)}%
          </span>
        )}
      </div>
    </div>
  );
}
