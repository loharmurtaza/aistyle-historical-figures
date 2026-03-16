import { STATS } from "@/lib/constants";

export default function HeroLeft() {
  return (
    <div className="flex-1 bg-cream flex flex-col justify-center px-10 lg:px-20 py-20">
      {/* Label */}
      <div className="flex items-center gap-3 mb-8">
        <span className="block w-8 h-px bg-dark/40" />
        <span className="text-[10px] font-sans font-medium tracking-[0.2em] text-dark/55">
          AI PORTRAIT STUDIO
        </span>
      </div>

      {/* Headline */}
      <h1 className="font-serif text-5xl lg:text-6xl font-bold leading-[1.1] mb-6 text-dark">
        Portraits of
        <br />
        <span className="text-gold italic">History&apos;s Finest</span>
        <br />
        in Any Style
      </h1>

      {/* Subheading */}
      <p className="font-sans text-dark/65 text-base lg:text-lg leading-relaxed max-w-sm mb-14">
        Describe a historical figure, pick an artistic style, and watch AI
        render them in seconds.
      </p>

      {/* Stats */}
      <div className="flex gap-10 lg:gap-14">
        {STATS.map(({ value, label }) => (
          <div key={label}>
            <p className="font-serif text-3xl font-bold text-dark">{value}</p>
            <p className="font-sans text-[11px] text-dark/55 mt-1 tracking-wide">
              {label}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
