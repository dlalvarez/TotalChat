import { HTMLAttributes, ReactNode } from 'react';
import { cn } from '../../lib/utils';
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <section className={cn('rounded-2xl border border-slate-200 bg-white p-5 shadow-soft', className)} {...props} />; }
export function SectionCard({ title, description, children }: { title: string; description?: string; children: ReactNode }) { return <Card><div className="mb-4"><h2 className="text-lg font-semibold text-slate-950">{title}</h2>{description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}</div>{children}</Card>; }
