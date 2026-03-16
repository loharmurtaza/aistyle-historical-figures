import { Crown, Zap, Palette, Swords } from "lucide-react";
import type { PortraitCardData } from "@/types";

const ICONS = {
  crown: Crown,
  lightning: Zap,
  palette: Palette,
  swords: Swords,
};

const BADGE_STYLES = {
  gold: "text-gold",
  cyan: "text-cyan-400",
  muted: "text-dark/50",
};

interface PortraitCardProps extends PortraitCardData {}

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:3001";

export default function PortraitCard({
  iconType,
  name,
  styleTag,
  styleBadgeVariant = "muted",
  bgDark,
  imageId,
}: PortraitCardProps) {
  const Icon = ICONS[iconType];

  const iconColorClass =
    iconType === "palette"
      ? "text-orange-400"
      : iconType === "lightning"
      ? "text-gold"
      : iconType === "crown"
      ? "text-gold"
      : "text-dark/60";

  return (
    <div
      className={`relative flex flex-col justify-between min-h-[220px] overflow-hidden ${
        bgDark ? "bg-dark-card" : "bg-parchment"
      }`}
    >
      {/* Background image or icon */}
      {imageId != null ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={`${BACKEND_URL}/api/gallery/${imageId}/image`}
          alt={name}
          className="absolute inset-0 w-full h-full object-cover"
        />
      ) : (
        <div className="flex-1 flex items-center justify-center p-6 py-6">
          <Icon
            size={48}
            strokeWidth={1.25}
            className={bgDark ? "text-gold/80" : iconColorClass}
          />
        </div>
      )}

      {/* Card footer */}
      <div
        className={`relative mt-auto px-4 py-3 ${
          imageId != null
            ? "bg-gradient-to-t from-black/70 to-transparent pt-8"
            : ""
        }`}
      >
        <p
          className={`font-serif italic text-base leading-tight ${
            imageId != null ? "text-cream" : bgDark ? "text-cream/90" : "text-dark"
          }`}
        >
          {name}
        </p>
        <p
          className={`text-[10px] font-sans tracking-[0.16em] mt-1 ${
            imageId != null
              ? BADGE_STYLES[styleBadgeVariant]
              : bgDark
              ? BADGE_STYLES[styleBadgeVariant]
              : "text-dark/50"
          }`}
        >
          {styleTag}
        </p>
      </div>
    </div>
  );
}
