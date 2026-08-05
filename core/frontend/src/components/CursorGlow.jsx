import { useEffect, useRef } from "react";

/**
 * Mount this once, near the top of your root layout (right after the
 * opening tag of your outermost div in App.jsx), and it sits fixed behind
 * all content, casting a soft teal glow that follows the pointer.
 * This is the ambient-life effect Linear/Vercel-style pages use — it makes
 * a flat black background feel alive without costing real motion budget,
 * since it's a single transform update, not a full re-render.
 *
 * Usage: <CursorGlow /> — no props needed, drop it in once.
 * On touch devices / prefers-reduced-motion, it stays parked at a fixed
 * spot instead of tracking, so it never fights with scrolling on mobile.
 */
export default function CursorGlow() {
  const glowRef = useRef(null);

  useEffect(() => {
    const node = glowRef.current;
    if (!node) return;

    const prefersReducedMotion =
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    const isTouchDevice = window.matchMedia?.("(pointer: coarse)").matches;

    if (prefersReducedMotion || isTouchDevice) return;

    let targetX = window.innerWidth / 2;
    let targetY = window.innerHeight * 0.3;
    let currentX = targetX;
    let currentY = targetY;
    let raf;

    const handleMove = (e) => {
      targetX = e.clientX;
      targetY = e.clientY;
    };

    // Lerp toward the pointer each frame instead of snapping directly to
    // it — the slight lag is what makes it read as "ambient" rather than
    // a cursor-tracking gimmick.
    const animate = () => {
      currentX += (targetX - currentX) * 0.06;
      currentY += (targetY - currentY) * 0.06;
      node.style.transform = `translate3d(${currentX - 300}px, ${currentY - 300}px, 0)`;
      raf = requestAnimationFrame(animate);
    };

    window.addEventListener("mousemove", handleMove);
    raf = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener("mousemove", handleMove);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
    >
      <div
        ref={glowRef}
        className="absolute h-[600px] w-[600px] rounded-full bg-ai/[0.07] blur-[120px]"
        style={{ top: 0, left: 0 }}
      />
    </div>
  );
}