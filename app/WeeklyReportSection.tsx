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
    <div className="mt-8 pt-8 border-t border-zinc-200">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-medium text-zinc-700">AI-veckorapport</h2>
          <p className="text-xs text-zinc-400 mt-0.5">Genererar en ledningssammanfattning baserat på all gästfeedback</p>
        </div>
        <Button onClick={generate} disabled={state === 'loading'} size="sm">
          {state === 'loading' ? 'Genererar…' : state === 'done' ? 'Generera igen' : 'Generera veckorapport'}
        </Button>
      </div>

      {state === 'loading' && (
        <div className="bg-white border border-zinc-200 rounded-lg p-6 animate-pulse">
          <div className="h-3 bg-zinc-100 rounded w-1/3 mb-3" />
          <div className="h-3 bg-zinc-100 rounded w-full mb-2" />
          <div className="h-3 bg-zinc-100 rounded w-5/6 mb-2" />
          <div className="h-3 bg-zinc-100 rounded w-4/6" />
        </div>
      )}

      {state === 'done' && (
        <div className="bg-white border border-zinc-200 rounded-lg p-6">
          <pre className="text-sm text-zinc-700 whitespace-pre-wrap font-sans leading-relaxed">{report}</pre>
        </div>
      )}

      {state === 'error' && (
        <p className="text-sm text-red-500">Något gick fel. Kontrollera att ANTHROPIC_API_KEY är satt.</p>
      )}
    </div>
  );
}
