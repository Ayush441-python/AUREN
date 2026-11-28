"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ButtonLink } from "@/components/ui/Button";
import SceneFallback from "@/components/three/SceneFallback";
import { usePrefersReducedMotion } from "@/lib/motion";
import { STORY_STEPS, clamp, storyState } from "@/lib/story";
import StoryProgress, { type StoryProgressHandle } from "./StoryProgress";

const ArchitectureCanvas = dynamic(
  () => import("@/components/three/ArchitectureCanvas"),
  {
    ssr: false,
    loading: () => (
      <div className="h-full w-full">
        <SceneFallback />
      </div>
    ),
  }
);

export default function ArchitectureStory() {
  const sectionRef = useRef<HTMLElement>(null);
  const pinRef = useRef<HTMLDivElement>(null);
  const panelRefs = useRef<(HTMLDivElement | null)[]>([]);
  const progressRef = useRef<StoryProgressHandle>(null);
  const scrollTriggerRef = useRef<ScrollTrigger | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [canvasActive, setCanvasActive] = useState(false);
  const prefersReducedMotion = usePrefersReducedMotion();

  const goToStep = useCallback((index: number) => {
    const target = Math.round(clamp(index, 0, STORY_STEPS.length - 1));

    if (storyState.reducedMotion || !scrollTriggerRef.current) {
      document
        .getElementById(`story-step-${STORY_STEPS[target].id}`)
        ?.scrollIntoView({ behavior: "auto", block: "start" });
      return;
    }

    const trigger = scrollTriggerRef.current;
    const stepProgress = target / (STORY_STEPS.length - 1);
    trigger.scroll(trigger.start + stepProgress * (trigger.end - trigger.start));
  }, []);

  useEffect(() => {
    const section = sectionRef.current;
    const pin = pinRef.current;
    if (!section || !pin) return;

    const reducedByMedia = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const reduced = prefersReducedMotion || reducedByMedia;

    storyState.reducedMotion = reduced;
    storyState.mouseX = 0;
    storyState.mouseY = 0;

    if (reduced) {
      storyState.progress = 0;
      storyState.active = 0;
      queueMicrotask(() => setActiveStep(0));
      progressRef.current?.setProgress(0);
    }

    const handlePointerMove = (event: PointerEvent) => {
      const rect = section.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      storyState.mouseX = clamp(((event.clientX - rect.left) / rect.width) * 2 - 1, -1, 1);
      storyState.mouseY = clamp(((event.clientY - rect.top) / rect.height) * 2 - 1, -1, 1);
    };

    const handlePointerLeave = () => {
      storyState.mouseX = 0;
      storyState.mouseY = 0;
    };

    section.addEventListener("pointermove", handlePointerMove, { passive: true });
    section.addEventListener("pointerleave", handlePointerLeave);

    const observer = new IntersectionObserver(
      ([entry]) => {
        const visible = Boolean(entry?.isIntersecting);
        storyState.visible = visible;
        setCanvasActive(visible);
      },
      { threshold: 0.01, rootMargin: "10% 0px 10% 0px" }
    );
    observer.observe(section);

    const cleanupRuntime = () => {
      section.removeEventListener("pointermove", handlePointerMove);
      section.removeEventListener("pointerleave", handlePointerLeave);
      observer.disconnect();
      storyState.progress = 0;
      storyState.active = 0;
      storyState.mouseX = 0;
      storyState.mouseY = 0;
      storyState.visible = true;
      storyState.reducedMotion = false;
      scrollTriggerRef.current = null;
      progressRef.current?.setProgress(0);
    };

    if (reduced) return cleanupRuntime;

    gsap.registerPlugin(ScrollTrigger);

    const panels = panelRefs.current.filter(
      (panel): panel is HTMLDivElement => Boolean(panel)
    );
    if (panels.length !== STORY_STEPS.length) return cleanupRuntime;

    const updateProgress = (progress: number) => {
      const value = clamp(progress);
      storyState.progress = value;
      progressRef.current?.setProgress(value);

      const next = Math.min(
        STORY_STEPS.length - 1,
        Math.max(0, Math.round(value * (STORY_STEPS.length - 1)))
      );

      if (next !== storyState.active) {
        storyState.active = next;
        setActiveStep(next);
      }
    };

    const media = gsap.matchMedia();

    const buildSequence = (distance: number) => {
      const context = gsap.context(() => {
        gsap.set(panels, {
          autoAlpha: 0,
          y: 56,
          scale: 0.985,
          filter: "blur(10px)",
        });
        gsap.set(panels[0], {
          autoAlpha: 1,
          y: 0,
          scale: 1,
          filter: "blur(0px)",
        });

        const timeline = gsap.timeline({
          defaults: { ease: "none" },
          scrollTrigger: {
            trigger: section,
            pin: pin,
            pinSpacing: true,
            start: "top top",
            end: () => `+=${distance}`,
            scrub: 0.6,
            invalidateOnRefresh: true,
            anticipatePin: 1,
            onUpdate: (self) => updateProgress(self.progress),
            onRefresh: (self) => updateProgress(self.progress),
          },
        });

        scrollTriggerRef.current = timeline.scrollTrigger ?? null;

        for (let index = 0; index < STORY_STEPS.length - 1; index += 1) {
          const at = index + 0.15;
          timeline
            .to(
              panels[index],
              {
                autoAlpha: 0,
                y: -48,
                scale: 0.97,
                filter: "blur(8px)",
                duration: 0.35,
                ease: "power2.inOut",
              },
              at
            )
            .fromTo(
              panels[index + 1],
              {
                autoAlpha: 0,
                y: 56,
                scale: 1.025,
                filter: "blur(10px)",
              },
              {
                autoAlpha: 1,
                y: 0,
                scale: 1,
                filter: "blur(0px)",
                duration: 0.35,
                ease: "power2.out",
              },
              at
            );
        }

        const duration = { value: 0 };
        timeline.to(duration, { value: 1, duration: STORY_STEPS.length - 1 }, 0);
      }, section);

      return () => {
        context.revert();
        scrollTriggerRef.current = null;
      };
    };

    media.add("(min-width: 1024px)", () => buildSequence(5000));
    media.add("(max-width: 1023px)", () => buildSequence(3400));

    return () => {
      media.revert();
      cleanupRuntime();
    };
  }, [prefersReducedMotion]);

  return (
    <section
      ref={sectionRef}
      id="architecture"
      aria-label="AUREN architecture story"
      className="relative isolate w-full overflow-x-clip bg-obsidian"
    >
      <div
        ref={pinRef}
        className="relative h-svh min-h-[540px] w-full overflow-hidden motion-reduce:hidden"
      >
        <div className="pointer-events-none absolute inset-0" aria-hidden="true">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_45%,rgba(212,175,55,0.12),transparent_42%)]" />
          <div className="auren-grid auren-grid-fade absolute inset-0 opacity-30" />
          <div className="absolute inset-y-0 right-[-12%] w-full md:right-0 md:w-[72%]">
            <ArchitectureCanvas
              variant="story"
              active={canvasActive && !prefersReducedMotion}
              className="h-full w-full"
            />
          </div>
          <div className="absolute inset-0 bg-gradient-to-r from-obsidian via-obsidian/85 to-obsidian/20" />
          <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-obsidian via-obsidian/70 to-transparent" />
        </div>

        <div className="relative z-10 mx-auto flex h-full max-w-[1440px] flex-col px-5 pb-20 pt-12 sm:px-8 md:pb-16 md:pt-16 lg:px-16">
          <header>
            <p className="auren-eyebrow">
              {STORY_STEPS[0].label} / {STORY_STEPS[0].number}—
              {STORY_STEPS[STORY_STEPS.length - 1].number}
            </p>
            <h2 className="auren-display mt-3 max-w-xl text-3xl text-primary sm:text-4xl lg:text-5xl">
              Intelligence, layer by layer.
            </h2>
          </header>

          <div className="relative mt-auto w-full pb-4 md:mt-0 md:flex md:flex-1 md:items-center">
            <div className="relative min-h-[17rem] w-full sm:min-h-[19rem] md:max-w-[52%] md:pr-28 lg:max-w-[48%] lg:pr-40">
              {STORY_STEPS.map((step, index) => (
                <div
                  key={step.id}
                  ref={(node) => {
                    panelRefs.current[index] = node;
                  }}
                  className="absolute inset-x-0 top-0 will-change-transform"
                  style={{
                    opacity: index === 0 ? 1 : 0,
                    visibility: index === 0 ? "visible" : "hidden",
                  }}
                >
                  <p className="auren-eyebrow">
                    {step.number} / {step.label}
                  </p>
                  <h3 className="auren-display mt-4 text-4xl leading-[0.95] text-primary sm:text-5xl lg:text-[4.25rem]">
                    {step.headline}
                  </h3>
                  <p className="mt-5 max-w-lg text-sm leading-relaxed text-muted sm:text-base">
                    {step.description}
                  </p>
                  {index === STORY_STEPS.length - 1 && (
                    <ButtonLink
                      href="/dashboard"
                      variant="primary"
                      className="mt-8"
                    >
                      Launch AUREN
                    </ButtonLink>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        <StoryProgress
          ref={progressRef}
          active={activeStep}
          onSelect={goToStep}
          className="absolute bottom-20 right-5 z-20 md:bottom-1/2 md:right-10 md:translate-y-1/2 lg:right-16"
        />

        <p className="absolute bottom-5 left-5 z-20 max-w-[15rem] text-[0.6rem] leading-relaxed text-faint sm:left-8 lg:left-16">
          Illustrative 3D product visualization. Not live portfolio data.
        </p>
      </div>

      <div className="hidden border-t border-line bg-secondary/20 py-20 motion-reduce:block sm:py-28">
        <div className="mx-auto max-w-[1200px] px-5 sm:px-8 lg:px-16">
          <div className="max-w-3xl">
            <p className="auren-eyebrow">
              {STORY_STEPS[0].label} / Reduced motion overview
            </p>
            <h2 className="auren-display mt-4 text-4xl text-primary sm:text-5xl">
              {STORY_STEPS[0].headline}
            </h2>
            <p className="mt-5 text-sm leading-relaxed text-muted sm:text-base">
              {STORY_STEPS[0].description}
            </p>
          </div>

          <div className="mt-12 aspect-[16/10] w-full overflow-hidden border border-line bg-secondary sm:aspect-[21/9]">
            <SceneFallback />
          </div>

          <ol className="mt-14 grid gap-px border border-line bg-line md:grid-cols-2 lg:grid-cols-3">
            {STORY_STEPS.map((step, index) => (
              <li
                key={step.id}
                id={`story-step-${step.id}`}
                className="scroll-mt-24 bg-obsidian p-6 sm:p-8"
              >
                <p className="auren-eyebrow">
                  {step.number} / {step.label}
                </p>
                <h3 className="auren-display mt-4 text-3xl text-primary">
                  {step.headline}
                </h3>
                <p className="mt-4 text-sm leading-relaxed text-muted">
                  {step.description}
                </p>
                {index === STORY_STEPS.length - 1 && (
                  <ButtonLink
                    href="/dashboard"
                    variant="primary"
                    className="mt-7"
                  >
                    Launch AUREN
                  </ButtonLink>
                )}
              </li>
            ))}
          </ol>

          <p className="mt-8 text-[0.65rem] leading-relaxed text-faint">
            Illustrative 3D product visualization. Not live portfolio data.
          </p>
        </div>
      </div>
    </section>
  );
}
