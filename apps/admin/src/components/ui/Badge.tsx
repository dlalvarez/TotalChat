import type { ReactNode } from 'react';
import { cn } from '../../lib/utils';

type BadgeTone = 'neutral' | 'success' | 'warning' | 'info';

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: BadgeTone }) {
  const tones: Record<BadgeTone, string> = {
    neutral: 'bg-slate-100 text-slate-700',
    success: 'bg-emerald-50 text-emerald-700',
    warning: 'bg-amber-50 text-amber-700',
    info: 'bg-sky-50 text-sky-700',
  };

  return (
    <span className={cn('inline-flex rounded-full px-2.5 py-1 text-xs font-semibold', tones[tone])}>
      {children}
    </span>
  );
}
