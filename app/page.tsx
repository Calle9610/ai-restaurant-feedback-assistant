import Link from 'next/link';
import { getOverviewStats } from '@/lib/data';
import { getTheme } from '@/lib/restaurantConfig';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import WeeklyReportSection from './WeeklyReportSection';
import AppHeader from '@/components/AppHeader';

export const dynamic = 'force-dynamic';

const trendIcon = { up: '↑', down: '↓', stable: '→' };
const trendColor = { up: 'text-green-600', down: 'text-red-500', stable: 'text-muted-foreground' };
const trendLabel = { up: 'Uppåt', down: 'Nedåt', stable: 'Stabilt' };

export default async function HomePage() {
  const restaurants = await getOverviewStats();
  const totalReviews = restaurants.reduce((s, r) => s + r.totalReviews, 0);

  return (
    <div className="min-h-screen bg-background">
      <AppHeader activeHref="/" />

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-5">
          <p className="text-sm text-muted-foreground">
            Gästfeedback omvandlad till konkret handling – per restaurang, varje vecka
          </p>
          <span className="text-xs text-muted-foreground shrink-0 ml-4">{totalReviews} omdömen</span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {restaurants.map((r) => {
            const theme = getTheme(r.name);
            const total = r.sentiment.positive + r.sentiment.neutral + r.sentiment.negative || 1;
            return (
              <Link key={r.id} href={`/restaurant/${r.id}`}>
                <Card
                  className="hover:shadow-md transition-all cursor-pointer h-full overflow-hidden"
                  style={{ borderLeftWidth: 4, borderLeftColor: theme.accent }}
                >
                  <CardHeader className="pb-3 pt-4">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <CardTitle className="text-base font-mono" style={{ color: theme.text }}>{r.name}</CardTitle>
                        <p className="text-xs text-muted-foreground mt-0.5">{r.area}</p>
                      </div>
                      <span className={`text-sm font-bold shrink-0 ${trendColor[r.trend]}`} title={trendLabel[r.trend]}>
                        {trendIcon[r.trend]}
                        {Math.abs(r.trendDiff) > 0.05 ? ` ${Math.abs(r.trendDiff).toFixed(1)}` : ''}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-baseline gap-1.5 mb-4">
                      <span className="text-3xl font-bold">{r.avgRating.toFixed(1)}</span>
                      <span className="text-sm text-muted-foreground">/ 5</span>
                      <span className="text-xs text-muted-foreground ml-auto">{r.totalReviews} omdömen</span>
                    </div>
                    <div className="flex h-1.5 rounded-full overflow-hidden gap-px mb-2">
                      <div className="bg-green-400" style={{ width: `${(r.sentiment.positive / total) * 100}%` }} />
                      <div className="bg-amber-300" style={{ width: `${(r.sentiment.neutral / total) * 100}%` }} />
                      <div className="bg-red-400"   style={{ width: `${(r.sentiment.negative / total) * 100}%` }} />
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
