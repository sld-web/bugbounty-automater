import React from 'react';
import { cn } from '@/lib/utils';

interface DataTableProps<T> {
  columns: {
    key: string;
    label: string;
    render?: (item: T) => React.ReactNode;
    className?: string;
  }[];
  data: T[];
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  emptyMessage = 'No data available',
  className
}: DataTableProps<T>) {
  if (data.length === 0) {
    return (
      <div className={cn('glass-card p-8 text-center', className)}>
        <span className="text-white/40 font-mono text-sm">{emptyMessage}</span>
      </div>
    );
  }

  return (
    <div className={cn('overflow-hidden', className)}>
      <table className="w-full">
        <thead>
          <tr className="table-header">
            {columns.map((col) => (
              <th key={col.key} className={cn('py-3 px-4 text-left', col.className)}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={keyExtractor(item)} className="table-row">
              {columns.map((col) => (
                <td key={col.key} className={cn('table-cell', col.className)}>
                  {col.render
                    ? col.render(item)
                    : (item as Record<string, unknown>)[col.key] as React.ReactNode}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
