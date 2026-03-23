import { cn } from '@/lib/utils';

type StatusType = 'running' | 'pending' | 'completed' | 'failed' | 'idle' | 'paused';

interface StatusIndicatorProps {
  status: StatusType;
  size?: 'sm' | 'md';
  showLabel?: boolean;
  className?: string;
}

const statusConfig: Record<StatusType, { label: string; color: string; animate: boolean }> = {
  running: { label: 'RUNNING', color: 'bg-tertiary', animate: true },
  pending: { label: 'PENDING', color: 'bg-warning', animate: true },
  completed: { label: 'COMPLETED', color: 'bg-secondary', animate: false },
  failed: { label: 'FAILED', color: 'bg-error', animate: false },
  idle: { label: 'IDLE', color: 'bg-white/30', animate: false },
  paused: { label: 'PAUSED', color: 'bg-warning', animate: false },
};

export function StatusIndicator({ status, size = 'sm', showLabel = true, className }: StatusIndicatorProps) {
  const config = statusConfig[status];

  return (
    <span className={cn('flex items-center gap-2', className)}>
      <span
        className={cn(
          'rounded-full',
          config.color,
          size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2',
          config.animate && 'animate-pulse'
        )}
      />
      {showLabel && (
        <span className="text-xs font-mono uppercase tracking-wider text-white/70">
          {config.label}
        </span>
      )}
    </span>
  );
}
