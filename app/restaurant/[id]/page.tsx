import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getRestaurantWithReviews } from '@/lib/data';
import ReviewList from './ReviewList';

export const dynamic = 'force-dynamic';

export default async function RestaurantPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const result = await getRestaurantWithReviews(id);
  if (!result) notFound();

  const { restaurant, reviews } = result;
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
      <header className="bg-white border-b border-zinc-200 px-8 py-4">
        <Link href="/" className="text-xs text-zinc-400 hover:text-zinc-600 transition-colors">
          ← Alla restauranger
        </Link>
        <div className="mt-2">
          <h1 className="text-xl font-semibold tracking-tight">{restaurant.name}</h1>
          <p className="text-sm text-zinc-400">{restaurant.area}</p>
        </div>
        <div className="flex gap-5 mt-2 text-sm">
          <span className="font-semibold">{avgRating.toFixed(1)}<span className="text-zinc-400 font-normal"> / 5</span></span>
          <span className="text-zinc-400">{reviews.length} omdömen</span>
          <span className="text-green-600">{sentimentCounts.positive} positiva</span>
          <span className="text-amber-500">{sentimentCounts.neutral} neutrala</span>
          <span className="text-red-500">{sentimentCounts.negative} negativa</span>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-8 py-8">
        <ReviewList reviews={reviews} />
      </main>
    </div>
  );
}
