import PortraitComposer from "@/components/home/PortraitComposer";

export const metadata = {
  title: "Generate — ChronoCanvasAI",
};

export default function GeneratePage() {
  return (
    <div className="min-h-screen bg-cream pt-6">
      <div className="max-w-5xl mx-auto px-6 lg:px-10 pt-12 pb-6">
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
          Describe your historical figure, choose an art style, and let
          AI do the rest.
        </p>
      </div>
      <PortraitComposer />
    </div>
  );
}
