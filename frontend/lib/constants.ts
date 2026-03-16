import type { Style, Template, PortraitCardData, Stat } from "@/types";

export const STYLES: Style[] = [
  { id: "renaissance", label: "Renaissance" },
  { id: "anime", label: "Anime" },
  { id: "sketch", label: "Sketch" },
  { id: "watercolor", label: "Watercolor" },
  { id: "baroque", label: "Baroque" },
];

export const HERO_PORTRAIT_CARDS: PortraitCardData[] = [
  {
    iconType: "crown",
    name: "Cleopatra VII",
    styleTag: "ART NOUVEAU",
    styleBadgeVariant: "gold",
    bgDark: false,
  },
  {
    iconType: "lightning",
    name: "Nikola Tesla",
    styleTag: "CYBERPUNK",
    styleBadgeVariant: "gold",
    bgDark: true,
  },
  {
    iconType: "palette",
    name: "Da Vinci",
    styleTag: "WATERCOLOR",
    styleBadgeVariant: "gold",
    bgDark: true,
  },
  {
    iconType: "swords",
    name: "Raja Dahir",
    styleTag: "RENAISSANCE OIL",
    styleBadgeVariant: "gold",
    bgDark: false,
  },
];

export const QUICK_START_TEMPLATES: Template[] = [
  {
    figure: "Napoleon Bonaparte",
    style: "cyberpunk city",
    displayLabel: "Napoleon · Cyberpunk city",
  },
  {
    figure: "Cleopatra",
    style: "Marvel superhero",
    displayLabel: "Cleopatra · Marvel superhero",
  },
  {
    figure: "Raja Dahir",
    style: "Realistic",
    displayLabel: "Dahir · Realistic"
  },
  {
    figure: "Albert Einstein",
    style: "Studio Ghibli",
    displayLabel: "Einstein · Studio Ghibli",
  },
  {
    figure: "Genghis Khan",
    style: "watercolor",
    displayLabel: "Genghis Khan · watercolor",
  },
  {
    figure: "Marie Curie",
    style: "Art Deco poster",
    displayLabel: "Marie Curie · Art Deco poster",
  },
];

export const STATS: Stat[] = [
  { value: "10,000+", label: "Portraits created" },
  { value: "500+", label: "Historical figures" },
  { value: "24", label: "Art styles" },
];
