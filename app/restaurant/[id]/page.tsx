import { notFound } from 'next/navigation';
import { getRestaurantWithReviews } from '@/lib/data';
import { getTheme } from '@/lib/restaurantConfig';
import ReviewList from './ReviewList';
import AppHeader from '@/components/AppHeader';

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
      <AppHeader activeHref="/" />

      <div style={{ height: 3, background: theme.accent }} />

      <div className="bg-card border-b border-border px-6 py-5">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-mono font-bold tracking-tight" style={{ color: theme.text }}>
                {restaurant.name}
              </h1>
              <p className="text-sm text-muted-foreground mt-0.5">{restaurant.area}</p>
            </div>
            <div className="text-right shrink-0">
              <p className="text-3xl font-mono font-bold text-foreground">{avgRating.toFixed(1)}<span className="text-base text-muted-foreground font-normal"> / 5</span></p>
              <p className="text-xs text-muted-foreground mt-0.5">{reviews.length} omdömen</p>
            </div>
          </div>

          <div className="flex gap-4 mt-3 text-sm">
            <span className="text-green-600 font-medium">↑ {sentimentCounts.positive} positiva</span>
            <span className="text-amber-500 font-medium">→ {sentimentCounts.neutral} neutrala</span>
            <span className="text-red-500 font-medium">↓ {sentimentCounts.negative} negativa</span>
          </div>
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-6 py-8">
        <ReviewList reviews={reviews} />
      </main>
    </div>
  );
}
