import Link from 'next/link';
import { getInsights, getOverviewStats } from '@/lib/data';
import AppHeader from '@/components/AppHeader';

export const dynamic = 'force-dynamic';

const categoryLabels: Record<string, string> = {
  service: 'Service', food: 'Mat', waiting_time: 'Väntetid',
  atmosphere: 'Stämning', price: 'Pris', booking: 'Bokning', other: 'Övrigt',
};

export default async function InsightsPage() {
  const [insights, restaurants] = await Promise.all([getInsights(), getOverviewStats()]);
  const { totalReviews, overallSentiment, topComplaints, topPraise, sentimentByWeek } = insights;
  const posRate = totalReviews ? Math.round((overallSentiment.positive / totalReviews) * 100) : 0;
  const negRate = totalReviews ? Math.round((overallSentiment.negative / totalReviews) * 100) : 0;
  const maxWeekTotal = Math.max(...sentimentByWeek.map(w => w.positive + w.neutral + w.negative), 1);

  return (
    <div className="min-h-screen bg-background">
      <AppHeader activeHref="/insights" />

      <main className="max-w-5xl mx-auto px-8 py-8 space-y-8">

        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-card rounded-lg border border-border p-4 text-center">
            <p className="text-3xl font-bold">{totalReviews}</p>
            <p className="text-sm text-muted-foreground mt-1">Omdömen totalt</p>
          </div>
          <div className="bg-card rounded-lg border border-border p-4 text-center">
            <p className="text-3xl font-bold text-green-600">{posRate}%</p>
            <p className="text-sm text-muted-foreground mt-1">Positiva omdömen</p>
          </div>
          <div className="bg-card rounded-lg border border-border p-4 text-center">
            <p className="text-3xl font-bold text-red-500">{negRate}%</p>
            <p className="text-sm text-muted-foreground mt-1">Negativa omdömen</p>
          </div>
        </div>

        {/* Top complaints + top praise */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-card rounded-lg border border-border p-5">
            <h2 className="text-sm font-semibold text-red-600 uppercase tracking-wide mb-4">Topp klagomål</h2>
            <div className="space-y-3">
              {topComplaints.map(({ category, count }) => (
                <div key={category}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-foreground">{categoryLabels[category] ?? category}</span>
                    <span className="text-muted-foreground">{count}</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-red-400 rounded-full" style={{ width: `${(count / (topComplaints[0]?.count || 1)) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-card rounded-lg border border-border p-5">
            <h2 className="text-sm font-semibold text-green-600 uppercase tracking-wide mb-4">Topp beröm</h2>
            <div className="space-y-3">
              {topPraise.map(({ category, count }) => (
                <div key={category}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-foreground">{categoryLabels[category] ?? category}</span>
                    <span className="text-muted-foreground">{count}</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-green-400 rounded-full" style={{ width: `${(count / (topPraise[0]?.count || 1)) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sentiment over time */}
        <div className="bg-card rounded-lg border border-border p-5">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-5">Sentiment per vecka</h2>
          <div className="space-y-2">
            {sentimentByWeek.map(w => {
              const total = w.positive + w.neutral + w.negative || 1;
              const barWidth = (total / maxWeekTotal) * 100;
              return (
                <div key={w.week} className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-7 shrink-0">{w.week}</span>
                  <div className="flex-1 flex items-center gap-1">
                    <div className="flex h-5 rounded overflow-hidden gap-px" style={{ width: `${barWidth}%` }}>
                      <div className="bg-green-400" style={{ width: `${(w.positive / total) * 100}%` }} />
                      <div className="bg-amber-300" style={{ width: `${(w.neutral / total) * 100}%` }} />
                      <div className="bg-red-400"   style={{ width: `${(w.negative / total) * 100}%` }} />
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground w-6 text-right shrink-0">{total}</span>
                </div>
              );
            })}
          </div>
          <div className="flex gap-4 mt-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-400 inline-block" />Positiv</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-300 inline-block" />Neutral</span>
            <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400 inline-block" />Negativ</span>
          </div>
        </div>

        {/* Restaurant comparison */}
        <div className="bg-card rounded-lg border border-border p-5">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-4">Jämförelse</h2>
          <div className="space-y-3">
            {restaurants.map(r => {
              const total = r.sentiment.positive + r.sentiment.neutral + r.sentiment.negative || 1;
              return (
                <Link key={r.id} href={`/restaurant/${r.id}`} className="flex items-center gap-4 group">
                  <span className="w-32 text-sm font-medium text-foreground group-hover:text-primary transition-colors cursor-pointer shrink-0">{r.name}</span>
                  <span className="text-sm font-bold w-8 shrink-0">{r.avgRating.toFixed(1)}</span>
                  <div className="flex flex-1 h-4 rounded overflow-hidden gap-px">
                    <div className="bg-green-400" style={{ width: `${(r.sentiment.positive / total) * 100}%` }} />
                    <div className="bg-amber-300" style={{ width: `${(r.sentiment.neutral / total) * 100}%` }} />
                    <div className="bg-red-400"   style={{ width: `${(r.sentiment.negative / total) * 100}%` }} />
                  </div>
                  <span className="text-xs text-muted-foreground w-16 text-right shrink-0">{r.totalReviews} omdömen</span>
                </Link>
              );
            })}
          </div>
        </div>

      </main>
    </div>
  );
}
