import { useEffect, useState } from "react";

const INTRO_DURATION_MS = 2200;

/**
 * Plays every time the site loads — a single branded moment instead of a
 * wordy hero. No click, no scroll: it dismisses itself on a timer and the
 * parent (App.jsx) takes over from there to auto-scroll into the workspace.
 *
 * The progress fill isn't decorative — it reuses the "engine booting"
 * metaphor already established in TraceHero, so the intro feels like the
 * same system warming up, not an unrelated loading spinner bolted on.
 *
 * Respects prefers-reduced-motion by skipping straight to onComplete —
 * a forced multi-second animation is a real accessibility problem for
 * some visitors, not just a nice-to-have.
 */
export default function IntroScreen({ onComplete }) {
  const [progress, setProgress] = useState(0);
  const [exiting, setExiting] = useState(false);
  const [skip] = useState(
    () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
  );

  useEffect(() => {
    if (skip) {
      onComplete();
      return;
    }

    const start = performance.now();
    let raf;

    const tick = (now) => {
      const pct = Math.min(100, ((now - start) / INTRO_DURATION_MS) * 100);
      setProgress(pct);
      if (pct < 100) {
        raf = requestAnimationFrame(tick);
      } else {
        setExiting(true);
        setTimeout(onComplete, 450); // matches exit transition duration below
      }
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [skip, onComplete]);

  if (skip) return null;

  return (
    <div
      className={`
        fixed inset-0 z-[100] flex flex-col items-center justify-center
        bg-traceBg
        transition-all duration-[450ms] ease-in
        ${exiting ? "opacity-0 scale-[1.03] pointer-events-none" : "opacity-100 scale-100"}
      `}
    >
      <div className="pointer-events-none absolute inset-0 trace-grid opacity-30" />

      <div className="relative flex items-center gap-3">
        <span className="relative block h-3 w-3">
          <span className="block h-3 w-3 rounded-full bg-cyan" />
          <span className="absolute inset-0 h-3 w-3 animate-ping rounded-full bg-cyan opacity-50" />
        </span>
        <span className="font-mono-display text-3xl font-bold tracking-tight text-textPrimary sm:text-4xl">
          trace
        </span>
      </div>

      <p className="relative mt-4 font-mono text-xs uppercase tracking-[0.3em] text-textSecondary">
        Investigating your errors
      </p>

      <div className="relative mt-8 h-[2px] w-48 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-cyan transition-[width] duration-100 ease-linear"
          style={{ width: `${progress}%` }}
        />
      </div>

      <button
        onClick={() => {
          setExiting(true);
          setTimeout(onComplete, 450);
        }}
        className="absolute bottom-8 right-8 font-mono text-[11px] text-textDim transition-colors hover:text-textSecondary"
      >
        Skip →
      </button>
    </div>
  );
}