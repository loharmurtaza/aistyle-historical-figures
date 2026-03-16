export const metadata = {
  title: "Historical Figures — ChronoCanvasAI",
};

const FIGURES = [
  { name: "Napoleon Bonaparte", era: "1769–1821", region: "France" },
  { name: "Cleopatra VII", era: "69–30 BC", region: "Egypt" },
  { name: "Albert Einstein", era: "1879–1955", region: "Germany / USA" },
  { name: "Nikola Tesla", era: "1856–1943", region: "Serbia / USA" },
  { name: "Leonardo da Vinci", era: "1452–1519", region: "Italy" },
  { name: "Raja Dahir", era: "695–712 BC", region: "Sindh" },
  { name: "Genghis Khan", era: "1162–1227", region: "Mongolia" },
  { name: "Marie Curie", era: "1867–1934", region: "Poland / France" },
  { name: "William Shakespeare", era: "1564–1616", region: "England" },
  { name: "Joan of Arc", era: "1412–1431", region: "France" },
  { name: "Alexander the Great", era: "356–323 BC", region: "Macedonia" },
  { name: "Frida Kahlo", era: "1907–1954", region: "Mexico" },
];

export default function FiguresPage() {
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
          500+ historical figures available. Click any to generate a portrait.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-px bg-dark/10">
          {FIGURES.map(({ name, era, region }) => (
            <a
              key={name}
              href={`/generate?figure=${encodeURIComponent(name)}`}
              className="bg-cream p-6 hover:bg-parchment transition-colors duration-150 group"
            >
              <p className="font-serif text-base font-semibold text-dark group-hover:text-gold transition-colors duration-150">
                {name}
              </p>
              <p className="font-sans text-xs text-dark/50 mt-1">{era}</p>
              <p className="font-sans text-[10px] tracking-wider text-dark/40 mt-0.5 uppercase">
                {region}
              </p>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
