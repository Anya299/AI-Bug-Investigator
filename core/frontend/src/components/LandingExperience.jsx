import LandingNav from "./LandingNav";
import AuroraBackground from "./AuroraBackground";
import LandingHero from "./LandingHero";
import HowItWorks from "./HowItWorks";
import LiveDemoSection from "./LiveDemoSection";
import CTASection from "./CTASection";

/**
 * This is the entire first-visit experience. Nothing from
 * InvestigationWorkspace is imported or rendered here — the two are
 * fully separate trees, switched by App.jsx, not sections of one
 * scrollable page. That's what fixes "I land on the workspace and have
 * to scroll up to find the landing page."
 */
export default function LandingExperience({ onStartInvestigation }) {
  return (
    <div className="relative overflow-hidden bg-traceBg text-textPrimary">
      <AuroraBackground />
      <LandingNav onStartInvestigation={onStartInvestigation} />
      <LandingHero onStartInvestigation={onStartInvestigation} />
      <HowItWorks />
      <LiveDemoSection />
      <CTASection onStartInvestigation={onStartInvestigation} />
    </div>
  );
}