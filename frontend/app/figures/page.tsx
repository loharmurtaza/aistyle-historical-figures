import FiguresGrid from "@/components/figures/FiguresGrid";

export const metadata = {
  title: "Historical Figures — ChronoCanvasAI",
};

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

interface FigureItem {
  name: string;
  slug: string;
  born_year: number | null;
  died_year: number | null;
  origin: string | null;
  featured: boolean;
}

interface FiguresResponse {
  items: FigureItem[];
  total: number;
}

async function fetchFeatured(): Promise<FiguresResponse> {
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/figures?featured=true&page_size=50`,
      { cache: "no-store" }
    );
    if (!res.ok) throw new Error();
    return await res.json();
  } catch {
    return { items: [], total: 0 };
  }
}

export default async function FiguresPage() {
  const { items: featured } = await fetchFeatured();

  return (
    <div className="min-h-screen bg-cream">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 py-20">
        <div className="flex items-center gap-3 mb-6">
          <span className="block w-8 h-px bg-dark/40" />
          <span className="text-[10px] font-sans tracking-[0.2em] text-dark/55">
            THE COLLECTION
          </span>
        </div>
        <h1 className="font-serif text-4xl font-bold text-dark mb-4">
          Historical <span className="text-gold italic">Figures</span>
        </h1>
        <p className="font-sans text-dark/60 text-sm max-w-lg mb-16">
          Explore historical figures available. Click any to generate a portrait.
        </p>

        <FiguresGrid featured={featured} />
      </div>
    </div>
  );
}
