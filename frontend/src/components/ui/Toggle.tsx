import { cn } from '@/lib/utils';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

export function Toggle({ checked, onChange, label, disabled, size = 'md', className }: ToggleProps) {
  const sizes = {
    sm: { track: 'h-3 w-6', dot: 'h-2 w-2', translate: 'translate-x-3' },
    md: { track: 'h-4 w-8', dot: 'h-3 w-3', translate: 'translate-x-4' },
  };

  const sizeConfig = sizes[size];

  return (
    <label className={cn('flex items-center gap-3 cursor-pointer', disabled && 'opacity-50 cursor-not-allowed', className)}>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex items-center rounded-full transition-colors',
          sizeConfig.track,
          checked ? 'bg-tertiary' : 'bg-white/20'
        )}
      >
        <span
          className={cn(
            'inline-block rounded-full bg-white/80 transition-transform',
            sizeConfig.dot,
            checked ? sizeConfig.translate : 'translate-x-0.5'
          )}
        />
      </button>
      {label && (
        <span className="text-sm font-mono text-white/70">{label}</span>
      )}
    </label>
  );
}
