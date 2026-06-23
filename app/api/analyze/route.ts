import { NextRequest, NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';

const ai = new Anthropic();

export async function POST(req: NextRequest) {
  const { text, rating } = await req.json();

  if (!text || typeof rating !== 'number') {
    return NextResponse.json({ error: 'text och rating krävs' }, { status: 400 });
  }

  const response = await ai.messages.create({
    model: 'claude-haiku-4-5-20251001',
    max_tokens: 512,
    tools: [{
      name: 'analyze_review',
      description: 'Analysera ett restaurangomdöme',
      input_schema: {
        type: 'object',
        properties: {
          sentiment:        { type: 'string', enum: ['positive', 'neutral', 'negative'] },
          category:         { type: 'string', enum: ['service', 'food', 'waiting_time', 'atmosphere', 'price', 'booking', 'other'] },
          summary:          { type: 'string', description: '1–2 meningar på svenska' },
          suggested_action: { type: 'string', description: 'Konkret åtgärd för krogchefen, på svenska' },
        },
        required: ['sentiment', 'category', 'summary', 'suggested_action'],
      },
    }],
    tool_choice: { type: 'tool', name: 'analyze_review' },
    messages: [{
      role: 'user',
      content: `Analysera detta restaurangomdöme.\n\nBetyg: ${rating}/5\nText: "${text}"`,
    }],
  });

  const toolUse = response.content.find(
    (b): b is Anthropic.ToolUseBlock => b.type === 'tool_use'
  );

  if (!toolUse) {
    return NextResponse.json({ error: 'Oväntat svar från AI' }, { status: 500 });
  }

  return NextResponse.json(toolUse.input);
}
