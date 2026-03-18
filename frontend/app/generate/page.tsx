import PortraitComposer from "@/components/home/PortraitComposer";
import FigureInfoPanel from "@/components/figures/FigureInfoPanel";

export const metadata = {
  title: "Generate — ChronoCanvasAI",
};

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

interface FigureData {
  name: string;
  slug: string;
  description: string | null;
  born_year: number | null;
  died_year: number | null;
  era: string | null;
  origin: string | null;
  tags: string | null;
}

async function fetchFigure(slug: string): Promise<FigureData | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/figures/${slug}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default async function GeneratePage({
  searchParams,
}: {
  searchParams: { figure?: string; slug?: string };
}) {
  const figureName = searchParams?.figure ?? "";
  const slug = searchParams?.slug ?? "";

  const figureData = slug ? await fetchFigure(slug) : null;

  return (
    <div className="min-h-screen bg-cream pt-6">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 pt-12 pb-6">
        <div className="flex items-center gap-3 mb-4">
          <span className="block w-8 h-px bg-dark/40" />
          <span className="text-[10px] font-sans tracking-[0.2em] text-dark/55">
            AI PORTRAIT STUDIO
          </span>
        </div>
        <h1 className="font-serif text-4xl font-bold text-dark">
          Generate a <span className="text-gold italic">Portrait</span>
        </h1>
        <p className="mt-3 font-sans text-dark/60 text-sm max-w-lg">
          Describe your historical figure, choose an art style, and let AI do
          the rest.
        </p>
      </div>

      <div
        className={
          figureData
            ? "max-w-7xl mx-auto flex items-start gap-8 px-6 lg:px-10"
            : ""
        }
      >
        <div className={figureData ? "flex-1 min-w-0" : "w-full"}>
          <PortraitComposer initialPrompt={figureName} />
        </div>

        {figureData && (
          <div className="w-72 shrink-0 sticky top-6 pt-16">
            <FigureInfoPanel figure={figureData} />
          </div>
        )}
      </div>
    </div>
  );
}
