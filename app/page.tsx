import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { supabase } from "@/lib/supabase";

export const dynamic = "force-dynamic";

export default async function Home() {
  const { data: restaurants, error } = await supabase
    .from("restaurants")
    .select("id, name, area")
    .order("name");

  return (
    <div className="min-h-screen bg-zinc-50 p-8">
      <header className="mb-8">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-2xl font-semibold tracking-tight">Gästpuls</h1>
          <Badge variant="secondary">Demo</Badge>
        </div>
        <p className="text-sm text-zinc-500">
          Gästfeedback omvandlad till konkret handling – per restaurang, varje vecka.
        </p>
      </header>

      {error && (
        <p className="text-sm text-red-500 mb-4">
          Databasfel: {error.message}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-8">
        {restaurants?.map((r) => (
          <Card key={r.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">{r.name}</CardTitle>
              <CardDescription>{r.area}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-zinc-400">Omdömen laddas i M1</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Button>Generera veckorapport</Button>
    </div>
  );
}
