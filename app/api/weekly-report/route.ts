import { NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import { getWeeklyReportData } from '@/lib/data';
import { createServiceClient } from '@/lib/supabase';

const ai = new Anthropic();

export async function POST() {
  const data = await getWeeklyReportData();
  if (!data) return NextResponse.json({ error: 'Kunde inte hämta data' }, { status: 500 });

  const totalReviews = data.reduce((s, r) => s + r.total, 0);
  const totalPos = data.reduce((s, r) => s + r.sentiment.positive, 0);
  const totalNeg = data.reduce((s, r) => s + r.sentiment.negative, 0);

  const restaurantSummaries = data.map(r =>
    `${r.name} (${r.area}) – ${r.avgRating}/5, ${r.total} omdömen
  Sentiment: ${r.sentiment.positive} pos / ${r.sentiment.neutral} neutral / ${r.sentiment.negative} neg
  Topp beröm: ${r.topPositive.join(', ') || '–'}
  Topp klagomål: ${r.topNegative.join(', ') || '–'}
  AI-föreslagna åtgärder: ${r.suggestedActions.slice(0, 2).map((a, i) => `(${i + 1}) ${a}`).join(' ')}`
  ).join('\n\n');

  const prompt = `Du är en senior analytiker på Stockholm Krogbolag. Skriv en koncis veckorapport på svenska (max 350 ord) baserat på dessa gästfeedback-data.

KONCERNDATA
Totalt: ${totalReviews} omdömen | ${Math.round((totalPos / totalReviews) * 100)}% positiva | ${Math.round((totalNeg / totalReviews) * 100)}% negativa

PER RESTAURANG
${restaurantSummaries}

Rapporten ska ha:
1. Rubrik: "GÄSTPULS – VECKORAPPORT" + aktuellt datum
2. KONCERNÖVERSIKT (2-3 meningar om helheten)
3. Ett avsnitt per restaurang: nuläge + 1-2 konkreta åtgärder
4. VECKANS PRIORITERINGAR – top 3 åtgärder för hela koncernen

Var kortfattad och handlingsorienterad. Skriv som en erfaren affärsanalytiker.`;

  const response = await ai.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 1024,
    messages: [{ role: 'user', content: prompt }],
  });

  const reportText = response.content
    .filter(b => b.type === 'text')
    .map(b => (b as Anthropic.TextBlock).text)
    .join('');

  const now = new Date();
  const year = now.getFullYear();
  const week = Math.ceil(((now.getTime() - new Date(year, 0, 1).getTime()) / 86400000 + new Date(year, 0, 1).getDay() + 1) / 7);

  const db = createServiceClient();
  await db.from('weekly_summaries').insert({
    restaurant_id: null,
    week: `${year}-W${String(week).padStart(2, '0')}`,
    summary: reportText,
  });

  return NextResponse.json({ report: reportText });
}
