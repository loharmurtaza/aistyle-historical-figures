import HeroLeft from "./HeroLeft";
import HeroRight from "./HeroRight";
import type { Stat } from "@/types";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

const FALLBACK_STATS: Stat[] = [
  { value: "10,000+", label: "Portraits created" },
  { value: "500+", label: "Historical figures" },
  { value: "24", label: "Art styles" },
];

async function fetchStats(): Promise<Stat[]> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/stats`, { cache: "no-store" });
    if (!res.ok) return FALLBACK_STATS;
    const data = await res.json();
    return [
      { value: data.portraits_created.toLocaleString(), label: "Portraits created" },
      { value: data.unique_figures.toLocaleString(), label: "Historical figures" },
      { value: data.styles_available.toString(), label: "Art styles" },
    ];
  } catch {
    return FALLBACK_STATS;
  }
}

export default async function HeroSection() {
  const stats = await fetchStats();
  return (
    <section className="flex min-h-[85vh]">
      <HeroLeft stats={stats} />
      <HeroRight />
    </section>
  );
}
