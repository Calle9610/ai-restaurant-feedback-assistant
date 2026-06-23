import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Anon client – safe to use in browser and Server Components for reads
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Service role client – server-side only (seed scripts, AI pipeline)
// Never expose SUPABASE_SERVICE_ROLE_KEY to the browser
export function createServiceClient() {
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceKey) throw new Error("SUPABASE_SERVICE_ROLE_KEY is not set");
  return createClient(supabaseUrl, serviceKey, {
    auth: { persistSession: false },
  });
}
