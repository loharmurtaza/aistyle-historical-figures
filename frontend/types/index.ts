export interface Style {
  id: string;
  label: string;
}

export interface Template {
  figure: string;
  style: string;
  displayLabel: string;
}

export interface PortraitCardData {
  iconType: "crown" | "lightning" | "palette" | "swords";
  name: string;
  styleTag: string;
  styleBadgeVariant?: "gold" | "cyan" | "muted";
  bgDark: boolean;
  imageId?: number;
}

export interface GenerateRequest {
  figure: string;
  style?: string;
  enhance?: boolean;
}

export interface GenerateResponse {
  image_url: string;
  revised_prompt: string;
  enhanced_prompt: string;
  figure: string;
  figure_title: string;
  style: string;
}

export interface Stat {
  value: string;
  label: string;
}
