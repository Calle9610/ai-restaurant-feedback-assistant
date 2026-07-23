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

  return data.map((r) => {
    const reviews = r.reviews ?? [];
    const total = reviews.length;
    const avgRating =
      total > 0
        ? Math.round((reviews.reduce((s, rv) => s + rv.rating, 0) / total) * 10) / 10
        : 0;

    const recent = reviews.filter((rv) => now - new Date(rv.created_at).getTime() < FOUR_WEEKS);
    const prior = reviews.filter((rv) => {
      const age = now - new Date(rv.created_at).getTime();
      return age >= FOUR_WEEKS && age < FOUR_WEEKS * 2;
    });

    const avg = (arr: typeof reviews) =>
      arr.length ? arr.reduce((s, rv) => s + rv.rating, 0) / arr.length : null;

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

// ─── Insights ────────────────────────────────────────────────────────────────

export type CategoryCount = { category: Category; count: number };

export type InsightData = {
  totalReviews: number;
  overallSentiment: Record<Sentiment, number>;
  topComplaints: CategoryCount[];
  topPraise: CategoryCount[];
  sentimentByWeek: { week: string; sort: string; positive: number; neutral: number; negative: number }[];
};

function isoWeek(date: Date): { sort: string; label: string } {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
  const day = d.getUTCDay() || 7;
  d.setUTCDate(d.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const w = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
  return { sort: `${d.getUTCFullYear()}-W${String(w).padStart(2, '0')}`, label: `V${w}` };
}

export async function getInsights(): Promise<InsightData> {
  const { data: reviews } = await supabase
    .from('reviews')
    .select('created_at, review_analysis(sentiment, category)');

  if (!reviews) return { totalReviews: 0, overallSentiment: { positive: 0, neutral: 0, negative: 0 }, topComplaints: [], topPraise: [], sentimentByWeek: [] };

  const overallSentiment: Record<Sentiment, number> = { positive: 0, neutral: 0, negative: 0 };
  const negCat: Record<string, number> = {};
  const posCat: Record<string, number> = {};
  const weekMap: Record<string, { sort: string; positive: number; neutral: number; negative: number }> = {};

  for (const rv of reviews) {
    const a = Array.isArray(rv.review_analysis) ? rv.review_analysis[0] : rv.review_analysis;
    if (!a) continue;
    const s = a.sentiment as Sentiment;
    if (s in overallSentiment) overallSentiment[s]++;
    if (s === 'negative') negCat[a.category] = (negCat[a.category] ?? 0) + 1;
    if (s === 'positive') posCat[a.category] = (posCat[a.category] ?? 0) + 1;

    const { sort, label } = isoWeek(new Date(rv.created_at));
    if (!weekMap[label]) weekMap[label] = { sort, positive: 0, neutral: 0, negative: 0 };
    weekMap[label][s]++;
  }

  const toRanked = (map: Record<string, number>): CategoryCount[] =>
    Object.entries(map)
      .map(([category, count]) => ({ category: category as Category, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);

  const sentimentByWeek = Object.entries(weekMap)
    .sort(([, a], [, b]) => a.sort.localeCompare(b.sort))
    .map(([week, v]) => ({ week, ...v }));

  return { totalReviews: reviews.length, overallSentiment, topComplaints: toRanked(negCat), topPraise: toRanked(posCat), sentimentByWeek };
}

// ─── Weekly report data ───────────────────────────────────────────────────────

export async function getWeeklyReportData() {
  const { data: restaurants } = await supabase.from('restaurants').select('id, name, area');
  if (!restaurants) return null;

  const result = [];
  for (const r of restaurants) {
    const { data: reviews } = await supabase
      .from('reviews')
      .select('rating, text, review_analysis(sentiment, category, suggested_action)')
      .eq('restaurant_id', r.id);

    if (!reviews) continue;

    const total = reviews.length;
    const avgRating = total ? reviews.reduce((s, rv) => s + rv.rating, 0) / total : 0;
    const sent: Record<Sentiment, number> = { positive: 0, neutral: 0, negative: 0 };
    const negCat: Record<string, number> = {};
    const posCat: Record<string, number> = {};
    const negativeActions: string[] = [];

    for (const rv of reviews) {
      const a = Array.isArray(rv.review_analysis) ? rv.review_analysis[0] : rv.review_analysis;
      if (!a) continue;
      const s = a.sentiment as Sentiment;
      if (s in sent) sent[s]++;
      if (s === 'negative') {
        negCat[a.category] = (negCat[a.category] ?? 0) + 1;
        if (negativeActions.length < 3 && a.suggested_action) negativeActions.push(a.suggested_action);
      }
      if (s === 'positive') posCat[a.category] = (posCat[a.category] ?? 0) + 1;
    }

    const topNeg = Object.entries(negCat).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([c, n]) => `${c} (${n})`);
    const topPos = Object.entries(posCat).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([c, n]) => `${c} (${n})`);

    result.push({ name: r.name, area: r.area, avgRating: Math.round(avgRating * 10) / 10, total, sentiment: sent, topPositive: topPos, topNegative: topNeg, suggestedActions: negativeActions });
  }
  return result;
}

// ─────────────────────────────────────────────────────────────────────────────

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

  const reviews: Review[] = (raw ?? []).map((rv) => {
    const a = Array.isArray(rv.review_analysis) ? rv.review_analysis[0] : rv.review_analysis;
    return { id: rv.id, rating: rv.rating, text: rv.text, source: rv.source, created_at: rv.created_at, analysis: a ?? null };
  });

  return { restaurant, reviews };
}
