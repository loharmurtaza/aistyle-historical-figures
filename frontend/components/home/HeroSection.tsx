import HeroLeft from "./HeroLeft";
import HeroRight from "./HeroRight";

export default function HeroSection() {
  return (
    <section className="flex min-h-[85vh]">
      <HeroLeft />
      <HeroRight />
    </section>
  );
}
