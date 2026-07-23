'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';

export default function WeeklyReportSection() {
  const [state, setState] = useState<'idle' | 'loading' | 'done' | 'error'>('idle');
  const [report, setReport] = useState('');

  async function generate() {
    setState('loading');
    try {
      const res = await fetch('/api/weekly-report', { method: 'POST' });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error);
      setReport(json.report);
      setState('done');
    } catch {
      setState('error');
    }
  }

  return (
    <div className="mt-10 pt-8 border-t border-border">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h2 className="text-base font-semibold text-foreground">AI-veckorapport</h2>
          <p className="text-sm text-muted-foreground mt-0.5">
            Ledningssammanfattning genererad av Claude baserat på all gästfeedback
          </p>
        </div>
        <Button
          onClick={generate}
          disabled={state === 'loading'}
          className="shrink-0 bg-accent text-accent-foreground hover:bg-accent/90 cursor-pointer"
        >
          {state === 'loading' ? (
            <span className="flex items-center gap-2">
              <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Genererar…
            </span>
          ) : state === 'done' ? 'Generera igen' : 'Generera veckorapport'}
        </Button>
      </div>

      {state === 'loading' && (
        <div className="bg-card border border-border rounded-lg p-6 space-y-3 animate-pulse">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-3 bg-muted rounded" style={{ width: `${95 - i * 8}%` }} />
          ))}
        </div>
      )}

      {state === 'done' && (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <div className="bg-zinc-900 px-5 py-2.5 flex items-center justify-between">
            <span className="text-xs text-zinc-300 font-mono tracking-widest">GÄSTPULS · VECKORAPPORT</span>
            <span className="text-xs text-zinc-400">{new Date().toLocaleDateString('sv-SE')}</span>
          </div>
          <div className="p-6">
            <div className="prose prose-sm max-w-none">
              {report.split('\n').map((line, i) => {
                if (!line.trim()) return <div key={i} className="h-2" />;
                if (line.startsWith('GÄSTPULS') || line.match(/^[A-ZÅÄÖ\s–]+$/)) {
                  return <p key={i} className="text-xs font-mono font-bold text-muted-foreground uppercase tracking-widest mt-4 mb-1 first:mt-0">{line}</p>;
                }
                if (line.match(/^\d\./)) {
                  return <p key={i} className="text-sm text-foreground ml-3">• {line.replace(/^\d\./, '').trim()}</p>;
                }
                return <p key={i} className="text-sm text-foreground leading-relaxed">{line}</p>;
              })}
            </div>
          </div>
        </div>
      )}

      {state === 'error' && (
        <p className="text-sm text-destructive bg-destructive/5 border border-destructive/20 rounded-lg px-4 py-3">
          Något gick fel. Kontrollera att ANTHROPIC_API_KEY är satt i Vercel.
        </p>
      )}
    </div>
  );
}
