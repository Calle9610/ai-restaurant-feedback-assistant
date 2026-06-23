import Link from 'next/link';
import { getOverviewStats } from '@/lib/data';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import WeeklyReportSection from './WeeklyReportSection';

export const dynamic = 'force-dynamic';

const trendIcon = { up: '↑', down: '↓', stable: '→' };
const trendColor = { up: 'text-green-600', down: 'text-red-500', stable: 'text-zinc-400' };
const trendLabel = { up: 'Uppåt', down: 'Nedåt', stable: 'Stabilt' };

export default async function HomePage() {
  const restaurants = await getOverviewStats();
  const totalReviews = restaurants.reduce((s, r) => s + r.totalReviews, 0);

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="bg-white border-b border-zinc-200 px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold tracking-tight">Gästpuls</h1>
            <Badge variant="secondary">Demo</Badge>
          </div>
          <nav className="flex gap-1">
            <Link href="/" className="px-3 py-1.5 text-sm rounded-md bg-zinc-100 text-zinc-900 font-medium">Översikt</Link>
            <Link href="/insights" className="px-3 py-1.5 text-sm rounded-md text-zinc-500 hover:text-zinc-700 transition-colors">Insikter</Link>
          </nav>
        </div>
        <p className="text-sm text-zinc-500 mt-2">
          Gästfeedback omvandlad till konkret handling – per restaurang, varje vecka
        </p>
      </header>

      <main className="max-w-5xl mx-auto px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-sm font-medium text-zinc-500 uppercase tracking-wide">Restauranger</h2>
          <span className="text-sm text-zinc-400">{totalReviews} omdömen totalt</span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {restaurants.map((r) => {
            const total = r.sentiment.positive + r.sentiment.neutral + r.sentiment.negative || 1;
            return (
              <Link key={r.id} href={`/restaurant/${r.id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <CardTitle className="text-base">{r.name}</CardTitle>
                        <p className="text-xs text-zinc-400 mt-0.5">{r.area}</p>
                      </div>
                      <span className={`text-sm font-semibold shrink-0 ${trendColor[r.trend]}`} title={trendLabel[r.trend]}>
                        {trendIcon[r.trend]}{' '}
                        {r.trendDiff !== 0 && Math.abs(r.trendDiff) > 0.05
                          ? Math.abs(r.trendDiff).toFixed(1)
                          : ''}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-baseline gap-2 mb-4">
                      <span className="text-3xl font-bold">{r.avgRating.toFixed(1)}</span>
                      <span className="text-sm text-zinc-400">/ 5</span>
                      <span className="text-xs text-zinc-400 ml-auto">{r.totalReviews} omdömen</span>
                    </div>

                    {/* Sentiment bar */}
                    <div className="flex h-1.5 rounded-full overflow-hidden gap-px mb-2">
                      <div className="bg-green-400 transition-all" style={{ width: `${(r.sentiment.positive / total) * 100}%` }} />
                      <div className="bg-amber-300 transition-all" style={{ width: `${(r.sentiment.neutral / total) * 100}%` }} />
                      <div className="bg-red-400 transition-all" style={{ width: `${(r.sentiment.negative / total) * 100}%` }} />
                    </div>
                    <div className="flex gap-3 text-xs">
                      <span className="text-green-600">↑ {r.sentiment.positive}</span>
                      <span className="text-amber-500">→ {r.sentiment.neutral}</span>
                      <span className="text-red-500">↓ {r.sentiment.negative}</span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>

        <WeeklyReportSection />
      </main>
    </div>
  );
}
