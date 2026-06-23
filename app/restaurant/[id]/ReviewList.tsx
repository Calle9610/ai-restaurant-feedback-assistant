'use client';

import { useState } from 'react';
import type { Review, Sentiment, Category } from '@/lib/data';

const sentimentConfig: Record<Sentiment, { label: string; pill: string; badge: string }> = {
  positive: { label: 'Positiv', pill: 'bg-green-50 text-green-700 border-green-200',  badge: 'bg-green-100 text-green-800 border-green-200' },
  neutral:  { label: 'Neutral', pill: 'bg-amber-50 text-amber-700 border-amber-200',  badge: 'bg-amber-100 text-amber-800 border-amber-200' },
  negative: { label: 'Negativ', pill: 'bg-red-50 text-red-700 border-red-200',        badge: 'bg-red-100 text-red-800 border-red-200' },
};

const categoryLabels: Record<Category, string> = {
  service:      'Service',
  food:         'Mat',
  waiting_time: 'Väntetid',
  atmosphere:   'Stämning',
  price:        'Pris',
  booking:      'Bokning',
  other:        'Övrigt',
};

function Stars({ n }: { n: number }) {
  return (
    <span className="text-amber-400 tracking-tight text-sm">
      {'★'.repeat(n)}{'☆'.repeat(5 - n)}
    </span>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('sv-SE', { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function ReviewList({ reviews }: { reviews: Review[] }) {
  const [activeSentiment, setActiveSentiment] = useState<Sentiment | 'all'>('all');
  const [activeCategory, setActiveCategory] = useState<Category | 'all'>('all');

  const filtered = reviews.filter((r) => {
    if (activeSentiment !== 'all' && r.analysis?.sentiment !== activeSentiment) return false;
    if (activeCategory !== 'all' && r.analysis?.category !== activeCategory) return false;
    return true;
  });

  const counts = {
    all:      reviews.length,
    positive: reviews.filter((r) => r.analysis?.sentiment === 'positive').length,
    neutral:  reviews.filter((r) => r.analysis?.sentiment === 'neutral').length,
    negative: reviews.filter((r) => r.analysis?.sentiment === 'negative').length,
  };

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 mb-6">
        {(['all', 'positive', 'neutral', 'negative'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setActiveSentiment(s)}
            className={`px-3 py-1 rounded-full text-sm font-medium border transition-colors ${
              activeSentiment === s
                ? 'bg-zinc-900 text-white border-zinc-900'
                : s === 'all'
                ? 'bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400'
                : `${sentimentConfig[s].pill} hover:opacity-80`
            }`}
          >
            {s === 'all' ? 'Alla' : sentimentConfig[s].label}
            <span className="ml-1.5 opacity-60 text-xs">{counts[s]}</span>
          </button>
        ))}

        <select
          value={activeCategory}
          onChange={(e) => setActiveCategory(e.target.value as Category | 'all')}
          className="ml-auto px-3 py-1.5 rounded-full text-sm border border-zinc-200 bg-white text-zinc-600 cursor-pointer focus:outline-none focus:border-zinc-400"
        >
          <option value="all">Alla kategorier</option>
          {(Object.entries(categoryLabels) as [Category, string][]).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
      </div>

      <p className="text-xs text-zinc-400 mb-4">{filtered.length} omdömen visas</p>

      {/* List */}
      <div className="space-y-3">
        {filtered.map((r) => (
          <div key={r.id} className="bg-white rounded-lg border border-zinc-200 p-4">
            <div className="flex items-center justify-between mb-2">
              <Stars n={r.rating} />
              <span className="text-xs text-zinc-400">{formatDate(r.created_at)}</span>
            </div>

            <p className="text-sm text-zinc-700 leading-relaxed mb-3">{r.text}</p>

            {r.analysis && (
              <div className="border-t border-zinc-100 pt-3 space-y-2">
                {/* Tags */}
                <div className="flex flex-wrap gap-1.5">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${sentimentConfig[r.analysis.sentiment].badge}`}>
                    {sentimentConfig[r.analysis.sentiment].label}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-zinc-100 text-zinc-600 border border-zinc-200">
                    {categoryLabels[r.analysis.category] ?? r.analysis.category}
                  </span>
                </div>

                {/* AI summary */}
                <p className="text-xs text-zinc-500 leading-relaxed">{r.analysis.summary}</p>

                {/* Suggested action – the key value prop */}
                <div className="bg-blue-50 border border-blue-100 rounded px-3 py-2">
                  <span className="text-xs font-semibold text-blue-700">Föreslagen åtgärd  </span>
                  <span className="text-xs text-blue-800">{r.analysis.suggested_action}</span>
                </div>
              </div>
            )}
          </div>
        ))}

        {filtered.length === 0 && (
          <p className="text-sm text-zinc-400 text-center py-12">Inga omdömen matchar filtret.</p>
        )}
      </div>
    </div>
  );
}
