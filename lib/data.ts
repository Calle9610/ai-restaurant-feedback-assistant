import { supabase } from './supabase';

export type Sentiment = 'positive' | 'neutral' | 'negative';
export type Category = 'service' | 'food' | 'waiting_time' | 'atmosphere' | 'price' | 'booking' | 'other';

export type ReviewAnalysis = {
  sentiment: Sentiment;
  category: Category;
  summary: string;
  suggested_action: string;
};

export type Review = {
  id: string;
  rating: number;
  text: string;
  source: string;
  created_at: string;
  analysis: ReviewAnalysis | null;
};

export type RestaurantStats = {
  id: string;
  name: string;
  area: string;
  avgRating: number;
  totalReviews: number;
  trend: 'up' | 'down' | 'stable';
  trendDiff: number;
  sentiment: Record<Sentiment, number>;
};

export async function getOverviewStats(): Promise<RestaurantStats[]> {
  const { data, error } = await supabase
    .from('restaurants')
    .select(`id, name, area, reviews(rating, created_at, review_analysis(sentiment))`)
    .order('name');

  if (error || !data) return [];

  const now = Date.now();
  const FOUR_WEEKS = 28 * 24 * 60 * 60 * 1000;

  return data.map((r: any) => {
    const reviews: any[] = r.reviews ?? [];
    const total = reviews.length;
    const avgRating =
      total > 0
        ? Math.round((reviews.reduce((s: number, rv: any) => s + rv.rating, 0) / total) * 10) / 10
        : 0;

    const recent = reviews.filter((rv: any) => now - new Date(rv.created_at).getTime() < FOUR_WEEKS);
    const prior = reviews.filter((rv: any) => {
      const age = now - new Date(rv.created_at).getTime();
      return age >= FOUR_WEEKS && age < FOUR_WEEKS * 2;
    });

    const avg = (arr: any[]) =>
      arr.length ? arr.reduce((s: number, rv: any) => s + rv.rating, 0) / arr.length : null;

    const recentAvg = avg(recent);
    const priorAvg = avg(prior);
    const diff = recentAvg !== null && priorAvg !== null ? recentAvg - priorAvg : 0;
    const trend: 'up' | 'down' | 'stable' = diff > 0.15 ? 'up' : diff < -0.15 ? 'down' : 'stable';

    const sentiment: Record<Sentiment, number> = { positive: 0, neutral: 0, negative: 0 };
    for (const rv of reviews) {
      const a = rv.review_analysis;
      const s = (Array.isArray(a) ? a[0]?.sentiment : a?.sentiment) as Sentiment | undefined;
      if (s && s in sentiment) sentiment[s]++;
    }

    return { id: r.id, name: r.name, area: r.area, avgRating, totalReviews: total, trend, trendDiff: diff, sentiment };
  });
}

export async function getRestaurantWithReviews(id: string) {
  const { data: restaurant, error } = await supabase
    .from('restaurants')
    .select('id, name, area')
    .eq('id', id)
    .single();

  if (error || !restaurant) return null;

  const { data: raw } = await supabase
    .from('reviews')
    .select(`id, rating, text, source, created_at, review_analysis(sentiment, category, summary, suggested_action)`)
    .eq('restaurant_id', id)
    .order('created_at', { ascending: false });

  const reviews: Review[] = (raw ?? []).map((rv: any) => {
    const a = Array.isArray(rv.review_analysis) ? rv.review_analysis[0] : rv.review_analysis;
    return { id: rv.id, rating: rv.rating, text: rv.text, source: rv.source, created_at: rv.created_at, analysis: a ?? null };
  });

  return { restaurant, reviews };
}
