import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getRestaurantWithReviews } from '@/lib/data';
import { getTheme } from '@/lib/restaurantConfig';
import ReviewList from './ReviewList';

export const dynamic = 'force-dynamic';

export default async function RestaurantPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await getRestaurantWithReviews(id);
  if (!result) notFound();

  const { restaurant, reviews } = result;
  const theme = getTheme(restaurant.name);
  const avgRating = reviews.length
    ? reviews.reduce((s, r) => s + r.rating, 0) / reviews.length
    : 0;

  const sentimentCounts = {
    positive: reviews.filter((r) => r.analysis?.sentiment === 'positive').length,
    neutral:  reviews.filter((r) => r.analysis?.sentiment === 'neutral').length,
    negative: reviews.filter((r) => r.analysis?.sentiment === 'negative').length,
  };

  return (
    <div className="min-h-screen bg-zinc-50">
      {/* Coloured header accent */}
      <div style={{ height: 4, background: theme.accent }} />

      <header className="bg-white border-b border-zinc-200 px-6 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-between mb-3">
            <Link href="/" className="text-xs text-zinc-400 hover:text-zinc-600 transition-colors">
              ← Översikt
            </Link>
            <nav className="flex gap-1">
              <Link href="/" className="px-3 py-1.5 text-sm rounded-md text-zinc-500 hover:text-zinc-800 transition-colors">Översikt</Link>
              <Link href="/insights" className="px-3 py-1.5 text-sm rounded-md text-zinc-500 hover:text-zinc-800 transition-colors">Insikter</Link>
            </nav>
          </div>

          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold tracking-tight" style={{ color: theme.text }}>
                {restaurant.name}
              </h1>
              <p className="text-sm text-zinc-400 mt-0.5">{restaurant.area}</p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-3xl font-bold">{avgRating.toFixed(1)}<span className="text-base text-zinc-400 font-normal"> / 5</span></p>
              <p className="text-xs text-zinc-400 mt-0.5">{reviews.length} omdömen</p>
            </div>
          </div>

          <div className="flex gap-4 mt-3 text-sm">
            <span className="text-green-600 font-medium">↑ {sentimentCounts.positive} positiva</span>
            <span className="text-amber-500 font-medium">→ {sentimentCounts.neutral} neutrala</span>
            <span className="text-red-500 font-medium">↓ {sentimentCounts.negative} negativa</span>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-8">
        <ReviewList reviews={reviews} />
      </main>
    </div>
  );
}
