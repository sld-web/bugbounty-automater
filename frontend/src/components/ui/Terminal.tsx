import { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

interface TerminalProps {
  logs: string[];
  className?: string;
  autoScroll?: boolean;
  maxLines?: number;
}

export function Terminal({ logs, className, autoScroll = true, maxLines = 100 }: TerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const displayLogs = logs.slice(-maxLines);

  return (
    <div
      ref={containerRef}
      className={cn('terminal rounded-lg p-4 h-64 overflow-auto', className)}
    >
      <div className="scanline-overlay" />
      <div className="relative z-10 space-y-1">
        {displayLogs.map((log, index) => (
          <div key={index} className="text-tertiary/80 font-mono text-xs leading-relaxed">
            <span className="text-white/30 mr-2">[{String(index + 1).padStart(3, '0')}]</span>
            {log}
          </div>
        ))}
      </div>
    </div>
  );
}

interface LiveTerminalProps {
  content: string;
  className?: string;
  showCursor?: boolean;
}

export function LiveTerminal({ content, className, showCursor = true }: LiveTerminalProps) {
  return (
    <div className={cn('terminal rounded-lg p-4 h-48 overflow-auto', className)}>
      <div className="scanline-overlay" />
      <div className="relative z-10">
        <div className="text-tertiary/80 font-mono text-xs whitespace-pre-wrap leading-relaxed">
          {content}
        </div>
        {showCursor && (
          <span className="absolute bottom-4 left-4 w-2 h-4 bg-tertiary animate-pulse" />
        )}
      </div>
    </div>
  );
}
