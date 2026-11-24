export type StoryStep = {
  id: string;
  number: string;
  label: string;
  headline: string;
  description: string;
};

export const STORY_STEPS: StoryStep[] = [
  {
    id: "architecture",
    number: "00",
    label: "The Architecture",
    headline: "Four layers. One clear view of risk.",
    description:
      "A single intelligence stack for reading volatility, exposure, relationships, and shock resilience as one connected system.",
  },
  {
    id: "risk",
    number: "01",
    label: "Risk Intelligence",
    headline: "Understand your risk.",
    description:
      "Quantify portfolio vulnerability through volatility, concentration, and historical drawdown analysis.",
  },
  {
    id: "exposure",
    number: "02",
    label: "Exposure & Allocation",
    headline: "See beyond allocation.",
    description:
      "Discover hidden concentration across individual assets, sectors, and portfolio exposures.",
  },
  {
    id: "correlation",
    number: "03",
    label: "Correlation Intelligence",
    headline: "Everything is connected.",
    description:
      "Understand how assets move together and uncover relationships that traditional diversification can overlook.",
  },
  {
    id: "stress",
    number: "04",
    label: "Stress Testing",
    headline: "Prepare for the unexpected.",
    description:
      "Explore historical market shocks and understand how your portfolio could respond under challenging conditions.",
  },
  {
    id: "reveal",
    number: "05",
    label: "The Workstation",
    headline: "Clarity in complexity.",
    description:
      "A deeper understanding of portfolio risk begins with AUREN.",
  },
];

export const STORY_LAYERS = STORY_STEPS.slice(1, 5);

export type StoryRuntime = {
  progress: number;
  active: number;
  mouseX: number;
  mouseY: number;
  visible: boolean;
  reducedMotion: boolean;
};

export const storyState: StoryRuntime = {
  progress: 0,
  active: 0,
  mouseX: 0,
  mouseY: 0,
  visible: true,
  reducedMotion: false,
};

export function clamp(value: number, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value));
}

export function smoothstep(value: number) {
  const t = clamp(value);
  return t * t * (3 - 2 * t);
}

export function segmentProgress(progress: number, start: number, end: number) {
  return smoothstep((progress - start) / (end - start));
}
