import { HERO_PORTRAIT_CARDS } from "@/lib/constants";
import PortraitCard from "./PortraitCard";

// One search term per card, matched to HERO_PORTRAIT_CARDS order
const FEATURED_FIGURES = ["Cleopatra", "Nikola Tesla", "Da Vinci", "Raja Dahir"];

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

interface FeaturedResult {
  search_term: string;
  id: number | null;
}

async function fetchFeaturedIds(): Promise<Record<string, number | null>> {
  try {
    const url = `${BACKEND_URL}/api/gallery/featured?figures=${encodeURIComponent(
      FEATURED_FIGURES.join(",")
    )}`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return {};
    const data: FeaturedResult[] = await res.json();
    return Object.fromEntries(data.map((d) => [d.search_term, d.id]));
  } catch {
    return {};
  }
}

export default async function HeroRight() {
  const featuredIds = await fetchFeaturedIds();

  const cards = HERO_PORTRAIT_CARDS.map((card, i) => ({
    ...card,
    imageId: featuredIds[FEATURED_FIGURES[i]] ?? undefined,
  }));

  return (
    <div className="flex-1 bg-dark hidden md:grid grid-cols-2 gap-px bg-dark/30">
      {cards.map((card) => (
        <PortraitCard key={card.name} {...card} />
      ))}
    </div>
  );
}
