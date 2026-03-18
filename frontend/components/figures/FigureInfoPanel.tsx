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

function formatYear(year: number): string {
  return year < 0 ? `${Math.abs(year)} BC` : `${year} AD`;
}

interface RowProps {
  label: string;
  value: string;
}

function InfoRow({ label, value }: RowProps) {
  return (
    <div className="py-3 border-b border-dark/10 flex items-baseline gap-4">
      <span className="text-[9px] font-sans tracking-[0.18em] text-dark/40 uppercase w-16 shrink-0">
        {label}
      </span>
      <span className="font-sans text-xs text-dark/75 leading-relaxed">{value}</span>
    </div>
  );
}

export default function FigureInfoPanel({ figure }: { figure: FigureData }) {
  const lifespan =
    figure.born_year != null && figure.died_year != null
      ? `${formatYear(figure.born_year)} – ${formatYear(figure.died_year)}`
      : figure.born_year != null
      ? `b. ${formatYear(figure.born_year)}`
      : figure.died_year != null
      ? `d. ${formatYear(figure.died_year)}`
      : null;

  const tags = figure.tags
    ? figure.tags.split(",").map((t) => t.trim()).filter(Boolean)
    : [];

  return (
    <div className="border border-dark/15 bg-cream">
      {/* Panel header */}
      <div className="px-5 py-4 border-b border-dark/15 flex items-center gap-2">
        <span className="block w-4 h-px bg-gold" />
        <span className="text-[9px] font-sans tracking-[0.22em] text-dark/45 uppercase">
          About this figure
        </span>
      </div>

      {/* Figure name */}
      <div className="px-5 pt-5 pb-3 border-b border-dark/10">
        <h2 className="font-serif text-lg font-semibold text-dark leading-snug">
          {figure.name}
        </h2>
        {figure.description && (
          <p className="mt-2 font-serif italic text-dark/55 text-sm leading-relaxed">
            {figure.description}
          </p>
        )}
      </div>

      {/* Details */}
      <div className="px-5">
        {lifespan && <InfoRow label="Lived" value={lifespan} />}
        {figure.era && <InfoRow label="Era" value={figure.era} />}
        {figure.origin && <InfoRow label="Origin" value={figure.origin} />}
      </div>

      {/* Tags */}
      {tags.length > 0 && (
        <div className="px-5 py-4">
          <span className="text-[9px] font-sans tracking-[0.18em] text-dark/40 uppercase block mb-2">
            Known for
          </span>
          <div className="flex flex-wrap gap-1.5">
            {tags.map((tag) => (
              <span
                key={tag}
                className="text-[10px] font-sans text-dark/60 border border-dark/15 px-2 py-0.5 capitalize"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
