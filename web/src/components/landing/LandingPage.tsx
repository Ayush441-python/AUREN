"use client";

import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Lenis from "lenis";
import { usePrefersReducedMotion } from "@/lib/motion";
import ArchitectureStory from "@/components/landing/ArchitectureStory";
import { CapabilitiesSection } from "@/components/landing/CapabilitiesSection";
import { FinalCta } from "@/components/landing/FinalCta";
import { Hero } from "@/components/landing/Hero";
import { LandingNav } from "@/components/landing/LandingNav";
import { ProductPreview } from "@/components/landing/ProductPreview";
import { SiteFooter } from "@/components/landing/SiteFooter";
import { TechnologySection } from "@/components/landing/TechnologySection";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

export function LandingPage() {
  const reducedMotion = usePrefersReducedMotion();

  useEffect(() => {
    if (reducedMotion) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (window.matchMedia("(pointer: coarse)").matches) return;

    const lenis = new Lenis({
      duration: 1.05,
      smoothWheel: true,
    });

    const updateScrollTrigger = () => ScrollTrigger.update();
    lenis.on("scroll", updateScrollTrigger);

    const tick = (time: number) => {
      lenis.raf(time * 1000);
    };
    gsap.ticker.add(tick);

    return () => {
      gsap.ticker.remove(tick);
      lenis.off("scroll", updateScrollTrigger);
      lenis.destroy();
    };
  }, [reducedMotion]);

  return (
    <>
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:border focus:border-gold/60 focus:bg-elevated focus:px-4 focus:py-2 focus:text-sm focus:text-primary"
      >
        Skip to content
      </a>
      <LandingNav />
      <main id="main" className="relative">
        <Hero />
        <ArchitectureStory />
        <TechnologySection />
        <CapabilitiesSection />
        <ProductPreview />
        <FinalCta />
      </main>
      <SiteFooter />
    </>
  );
}

export default LandingPage;
