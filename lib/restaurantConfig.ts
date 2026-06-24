export type RestaurantTheme = {
  accent: string;
  bg: string;
  border: string;
  text: string;
};

const themes: Record<string, RestaurantTheme> = {
  'Tennstopet':       { accent: '#B45309', bg: '#FFFBEB', border: '#FCD34D', text: '#92400E' },
  'Kommendören':      { accent: '#1D4ED8', bg: '#EFF6FF', border: '#93C5FD', text: '#1E3A8A' },
  'Tako':             { accent: '#0F766E', bg: '#F0FDFA', border: '#5EEAD4', text: '#134E4A' },
  'Tennstopet Grill': { accent: '#C2410C', bg: '#FFF7ED', border: '#FDBA74', text: '#9A3412' },
  'Kapten Jack':      { accent: '#0369A1', bg: '#F0F9FF', border: '#7DD3FC', text: '#0C4A6E' },
};

const fallback: RestaurantTheme = { accent: '#6B7280', bg: '#F9FAFB', border: '#D1D5DB', text: '#374151' };

export function getTheme(name: string): RestaurantTheme {
  return themes[name] ?? fallback;
}
