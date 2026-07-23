export type RestaurantTheme = {
  accent: string;
  bg: string;
  border: string;
  text: string;
};

const themes: Record<string, RestaurantTheme> = {
  'Tunnbindaren':       { accent: '#E16241', bg: '#FEF0EB', border: '#F0A48D', text: '#7A2D12' },
  'Envoyén':            { accent: '#A20000', bg: '#FFF0F0', border: '#D97070', text: '#6B0000' },
  'Kobo':               { accent: '#000000', bg: '#F5F5F5', border: '#A1A1AA', text: '#18181B' },
  'Tunnbindaren Grill': { accent: '#DF5327', bg: '#FDEEE7', border: '#ED9475', text: '#78260E' },
  'Ankarplatsen':       { accent: '#0F5250', bg: '#EDFAFA', border: '#5DA6A4', text: '#073533' },
};

const fallback: RestaurantTheme = { accent: '#6B7280', bg: '#F9FAFB', border: '#D1D5DB', text: '#374151' };

export function getTheme(name: string): RestaurantTheme {
  return themes[name] ?? fallback;
}
