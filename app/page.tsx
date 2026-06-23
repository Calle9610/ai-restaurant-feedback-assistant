import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const restaurants = [
  { name: "Tennstopet", area: "Vasastan", rating: 4.2, reviews: 38, trend: "up" },
  { name: "Kommendören", area: "Östermalm", rating: 3.8, reviews: 27, trend: "down" },
  { name: "Tako", area: "Södermalm", rating: 4.5, reviews: 41, trend: "up" },
];

export default function Home() {
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

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-8">
        {restaurants.map((r) => (
          <Card key={r.name}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">{r.name}</CardTitle>
              <CardDescription>{r.area}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <span className="text-2xl font-bold">{r.rating}</span>
                <Badge variant={r.trend === "up" ? "default" : "destructive"}>
                  {r.trend === "up" ? "↑" : "↓"} {r.reviews} omdömen
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Button>Generera veckorapport</Button>
    </div>
  );
}
