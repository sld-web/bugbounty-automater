import { cn } from '@/lib/utils';

interface ProgressBarProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  color?: 'secondary' | 'tertiary' | 'primary' | 'error';
  className?: string;
}

export function ProgressBar({
  value,
  max = 100,
  size = 'md',
  showLabel = false,
  color = 'secondary',
  className
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const heights = {
    sm: 'h-0.5',
    md: 'h-1',
    lg: 'h-2',
  };

  const colors = {
    secondary: 'bg-secondary',
    tertiary: 'bg-tertiary',
    primary: 'bg-primary',
    error: 'bg-error',
  };

  return (
    <div className={cn('w-full', className)}>
      <div className={cn('progress-bar', heights[size])}>
        <div
          className={cn('progress-bar-fill transition-all duration-500', colors[color])}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-mono text-white/50 mt-1 block">
          {Math.round(percentage)}%
        </span>
      )}
    </div>
  );
}
