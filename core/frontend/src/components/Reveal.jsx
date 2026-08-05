import { useEffect, useRef, useState } from "react";

/**
 * Wrap any section in <Reveal> and it animates in the first time it enters
 * the viewport, instead of just being present on page load. This is the
 * single highest-leverage change for making a static page feel alive —
 * most premium sites (Linear, Vercel, Stripe) reveal content on scroll
 * rather than rendering everything flat from the first frame.
 *
 * Usage:
 *   <Reveal><YourSection /></Reveal>
 *   <Reveal direction="left" delay={150}><Card /></Reveal>
 *
 * Props:
 *   direction — "up" (default) | "left" | "right" | "none"
 *   delay     — ms, stagger multiple Reveals by increasing this
 *   once      — if true (default), only animates the first time it's seen
 */
export default function Reveal({
  children,
  direction = "up",
  delay = 0,
  once = true,
  className = "",
}) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const prefersReducedMotion =
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

    if (prefersReducedMotion) {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          if (once) observer.unobserve(node);
        } else if (!once) {
          setVisible(false);
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [once]);

  const offset =
    direction === "left"
      ? "-translate-x-8"
      : direction === "right"
      ? "translate-x-8"
      : direction === "none"
      ? ""
      : "translate-y-8";

  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={`
        transition-all duration-700 ease-out
        ${visible ? "opacity-100 translate-x-0 translate-y-0" : `opacity-0 ${offset}`}
        ${className}
      `}
    >
      {children}
    </div>
  );
}