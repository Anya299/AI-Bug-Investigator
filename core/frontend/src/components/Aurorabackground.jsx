import { useEffect, useRef } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";

/**
 * Ambient depth, not a visible shape — this should read the way lighting
 * in a room does: you feel it more than you see it. Opacity kept low,
 * blur kept high, drift kept slow so it never competes with the content.
 */
export default function AuroraBackground() {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 40, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 40, damping: 20 });

  const blob1X = useTransform(springX, (v) => v * 0.015);
  const blob1Y = useTransform(springY, (v) => v * 0.015);
  const blob2X = useTransform(springX, (v) => v * -0.01);
  const blob2Y = useTransform(springY, (v) => v * -0.01);

  const reducedMotion = useRef(
    typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
  );

  useEffect(() => {
    if (reducedMotion.current) return;
    const handleMove = (e) => {
      mouseX.set(e.clientX - window.innerWidth / 2);
      mouseY.set(e.clientY - window.innerHeight / 2);
    };
    window.addEventListener("mousemove", handleMove);
    return () => window.removeEventListener("mousemove", handleMove);
  }, [mouseX, mouseY]);

  const drift = reducedMotion.current ? {} : { scale: [1, 1.05, 1] };

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      <motion.div
        style={{ x: blob1X, y: blob1Y }}
        animate={drift}
        transition={{ duration: 16, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -top-40 left-1/4 h-[560px] w-[560px] rounded-full bg-ai/[0.06] blur-[160px]"
      />
      <motion.div
        style={{ x: blob2X, y: blob2Y }}
        animate={drift}
        transition={{ duration: 20, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        className="absolute bottom-0 right-1/4 h-[480px] w-[480px] rounded-full bg-textSecondary/[0.035] blur-[160px]"
      />
    </div>
  );
}