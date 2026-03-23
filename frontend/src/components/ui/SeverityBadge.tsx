import { cn } from '@/lib/utils';

type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

interface SeverityBadgeProps {
  severity: Severity;
  size?: 'sm' | 'md';
  className?: string;
}

const severityConfig: Record<Severity, { label: string; className: string }> = {
  critical: { label: 'CRITICAL', className: 'badge-critical' },
  high: { label: 'HIGH', className: 'badge-high' },
  medium: { label: 'MEDIUM', className: 'badge-medium' },
  low: { label: 'LOW', className: 'badge-low' },
  info: { label: 'INFO', className: 'badge-info' },
};

export function SeverityBadge({ severity, size = 'sm', className }: SeverityBadgeProps) {
  const config = severityConfig[severity];

  return (
    <span
      className={cn(
        'badge rounded',
        config.className,
        size === 'md' && 'px-3 py-1 text-xs',
        className
      )}
    >
      {config.label}
    </span>
  );
}
