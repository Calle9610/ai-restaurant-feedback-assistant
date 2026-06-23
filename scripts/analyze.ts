import Anthropic from '@anthropic-ai/sdk';
import { createServiceClient } from '../lib/supabase';

const ai = new Anthropic();
const db = createServiceClient();

const BATCH_SIZE = 30;

type Analysis = {
  review_index: number;
  sentiment: 'positive' | 'neutral' | 'negative';
  category: 'service' | 'food' | 'waiting_time' | 'atmosphere' | 'price' | 'booking' | 'other';
  summary: string;
  suggested_action: string;
};

const analysisTool: Anthropic.Tool = {
  name: 'save_analyses',
  description: 'Spara analysresultat för en batch av restaurangomdömen',
  input_schema: {
    type: 'object',
    properties: {
      analyses: {
        type: 'array',
        items: {
          type: 'object',
          properties: {
            review_index:    { type: 'number', description: 'Index från inputlistan (0-baserat)' },
            sentiment:       { type: 'string', enum: ['positive', 'neutral', 'negative'] },
            category:        { type: 'string', enum: ['service', 'food', 'waiting_time', 'atmosphere', 'price', 'booking', 'other'] },
            summary:         { type: 'string', description: '1–2 meningar på svenska som sammanfattar omdömet' },
            suggested_action:{ type: 'string', description: 'Konkret åtgärd för krogchefen, börjar med ett verb, på svenska' },
          },
          required: ['review_index', 'sentiment', 'category', 'summary', 'suggested_action'],
        },
      },
    },
    required: ['analyses'],
  },
};

async function analyzeBatch(
  reviews: { id: string; rating: number; text: string }[]
): Promise<Analysis[]> {
  const numbered = reviews
    .map((r, i) => `[${i}] Betyg ${r.rating}/5: "${r.text}"`)
    .join('\n');

  const response = await ai.messages.create({
    model: 'claude-haiku-4-5-20251001',
    max_tokens: 4096,
    tools: [analysisTool],
    tool_choice: { type: 'tool', name: 'save_analyses' },
    messages: [{
      role: 'user',
      content: `Analysera dessa ${reviews.length} restaurangomdömen och returnera en analys per omdöme.\n\n${numbered}`,
    }],
  });

  const toolUse = response.content.find((b): b is Anthropic.ToolUseBlock => b.type === 'tool_use');
  if (!toolUse) throw new Error('Inget tool_use-svar från Claude');

  return (toolUse.input as { analyses: Analysis[] }).analyses;
}

async function main() {
  const { data: reviews, error: rErr } = await db
    .from('reviews')
    .select('id, rating, text')
    .order('created_at');

  if (rErr || !reviews) { console.error(rErr); process.exit(1); }

  const { data: existing } = await db.from('review_analysis').select('review_id');
  const done = new Set(existing?.map((r) => r.review_id) ?? []);
  const todo = reviews.filter((r) => !done.has(r.id));

  if (!todo.length) {
    console.log('Alla omdömen är redan analyserade.');
    return;
  }

  const total = Math.ceil(todo.length / BATCH_SIZE);
  console.log(`Analyserar ${todo.length} omdömen i ${total} batch(ar)…`);

  for (let i = 0; i < todo.length; i += BATCH_SIZE) {
    const batch = todo.slice(i, i + BATCH_SIZE);
    const n = Math.floor(i / BATCH_SIZE) + 1;
    process.stdout.write(`  Batch ${n}/${total} (${batch.length} st)… `);

    const analyses = await analyzeBatch(batch);

    const rows = analyses.map((a) => ({
      review_id:        batch[a.review_index].id,
      sentiment:        a.sentiment,
      category:         a.category,
      summary:          a.summary,
      suggested_action: a.suggested_action,
    }));

    const { error } = await db.from('review_analysis').insert(rows);
    if (error) { console.error('\n', error); process.exit(1); }

    console.log('✓');
  }

  console.log(`\n✓ Klart – ${todo.length} omdömen analyserade.`);
}

main();
