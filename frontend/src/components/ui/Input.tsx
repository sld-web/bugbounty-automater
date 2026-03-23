import React from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export function Input({ label, error, icon, className, ...props }: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block data-label mb-2">{label}</label>
      )}
      <div className="relative">
        {icon && (
          <span className="absolute left-0 top-1/2 -translate-y-1/2 text-white/30">
            {icon}
          </span>
        )}
        <input
          className={cn(
            'input bg-surface-lowest/50 rounded px-3 py-2',
            icon && 'pl-8',
            error && 'border-error',
            className
          )}
          {...props}
        />
      </div>
      {error && (
        <span className="text-error text-xs font-mono mt-1 block">{error}</span>
      )}
    </div>
  );
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: { value: string; label: string }[];
}

export function Select({ label, options, className, ...props }: SelectProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block data-label mb-2">{label}</label>
      )}
      <select
        className={cn(
          'w-full bg-surface-50 border-none rounded-lg text-sm font-mono py-3 px-4',
          'focus:ring-1 focus:ring-secondary outline-none cursor-pointer',
          className
        )}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export function Textarea({ label, className, ...props }: TextareaProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block data-label mb-2">{label}</label>
      )}
      <textarea
        className={cn(
          'w-full bg-surface-lowest border-0 border-b border-white/10 rounded-lg',
          'text-sm font-mono py-3 px-4 outline-none focus:border-tertiary resize-none',
          className
        )}
        {...props}
      />
    </div>
  );
}
