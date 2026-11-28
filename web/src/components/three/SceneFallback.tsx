import { STORY_LAYERS } from "@/lib/story";
import { cn } from "@/lib/cn";

type SceneFallbackProps = {
  variant?: "hero" | "story";
  className?: string;
};

const LAYER_NOTES = [
  "risk surface",
  "allocation map",
  "relationship graph",
  "shock simulation",
] as const;

export default function SceneFallback({ variant = "hero", className }: SceneFallbackProps) {
  return (
    <div
      className={cn(
        "relative flex h-full w-full items-center justify-center overflow-hidden bg-obsidian",
        className,
      )}
      role="img"
      aria-label="Simplified AUREN architecture diagram showing four stacked illustrative layers. This is not real-time 3D and does not show real portfolio data."
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_42%,rgba(212,175,55,0.09),transparent_58%)]"
      />
      <div
        className={cn(
          "relative w-full max-w-[620px] px-6 transition-transform duration-700",
          variant === "story" ? "scale-[0.94]" : "scale-100",
        )}
      >
        <div className="mb-8 flex items-center justify-between border-b border-[#302A20] pb-3">
          <span className="text-[10px] font-medium uppercase tracking-[0.34em] text-[#D4AF37]">
            Simplified architecture diagram
          </span>
          <span className="text-[9px] uppercase tracking-[0.22em] text-[#77736C]">
            Illustrative only · not portfolio data
          </span>
        </div>

        <div className="relative space-y-3 [perspective:900px]">
          {STORY_LAYERS.map((layer, index) => (
            <div
              key={layer.id}
              className="relative h-[68px] rounded-[14px] border border-[#302A20] bg-[#141311]/90 shadow-[0_18px_45px_rgba(0,0,0,0.42)]"
              style={{
                transform: `rotateX(56deg) rotateZ(-28deg) translateZ(${index * 10}px)`,
              }}
            >
              <div className="pointer-events-none absolute inset-[1px] rounded-[12px] border border-[#D4AF37]/25" />
              <div className="absolute left-5 top-1/2 flex -translate-y-1/2 items-center gap-4">
                <span className="text-[10px] font-medium tracking-[0.2em] text-[#EACB83]">
                  {layer.number}
                </span>
                <span className="text-[12px] font-medium tracking-[0.08em] text-[#F5F1E8]">
                  {layer.label}
                </span>
              </div>
              <div className="absolute right-6 top-1/2 -translate-y-1/2 text-[9px] uppercase tracking-[0.2em] text-[#A39D90]">
                {LAYER_NOTES[index]}
              </div>
              <div className="absolute bottom-3 left-5 h-px w-[38%] bg-gradient-to-r from-[#D4AF37]/70 to-transparent" />
            </div>
          ))}
        </div>

        <div className="mt-8 flex items-center gap-3 text-[9px] uppercase tracking-[0.24em] text-[#77736C]">
          <span className="h-px w-8 bg-[#D4AF37]/60" />
          <span>Four layers · one architecture</span>
        </div>
      </div>
    </div>
  );
}
