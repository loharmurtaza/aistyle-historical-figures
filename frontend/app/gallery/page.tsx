import GalleryClient from "@/components/gallery/GalleryClient";

export const metadata = {
  title: "Gallery — ChronoCanvasAI",
};

export default function GalleryPage() {
  return (
    <div className="min-h-screen bg-cream">
      <div className="max-w-7xl mx-auto px-6 lg:px-10 py-20">
        <div className="flex items-center gap-3 mb-6">
          <span className="block w-8 h-px bg-dark/40" />
          <span className="text-[10px] font-sans tracking-[0.2em] text-dark/55">
            COMMUNITY
          </span>
        </div>
        <h1 className="font-serif text-4xl font-bold text-dark mb-4">
          Portrait <span className="text-gold italic">Gallery</span>
        </h1>
        <p className="font-sans text-dark/60 text-sm max-w mb-16">
          Browse portraits created by The ChronoCanvasAI community. Each one
          rendered by DALL·E 3.
        </p>
        <GalleryClient />
      </div>
    </div>
  );
}
