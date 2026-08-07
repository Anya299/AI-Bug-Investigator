import { motion } from "framer-motion";
import { useRef } from "react";

// Three orbit paths, each with a node moving at a different speed and
// direction — this asymmetry is what reads as "thinking" rather than a
// single uniform pulse. The faint static rings give it structure even
// when reduced-motion disables the movement.
const ORBITS = [
  { size: 140, duration: 9, direction: 1, dot: "bg-cyan" },
  { size: 216, duration: 15, direction: -1, dot: "bg-cyan/70" },
  { size: 292, duration: 22, direction: 1, dot: "bg-textSecondary/60" },
];

export default function AICore() {
  const reducedMotion = useRef(
    typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
  );

  return (
    <div className="relative flex h-72 w-72 items-center justify-center sm:h-[340px] sm:w-[340px]">

      {/* structural orbit paths — visible even with motion off */}
      {ORBITS.map((o) => (
        <div
          key={`ring-${o.size}`}
          style={{ width: o.size, height: o.size }}
          className="absolute rounded-full border border-white/[0.06]"
        />
      ))}

      {/* orbiting nodes */}
      {!reducedMotion.current &&
        ORBITS.map((o) => (
          <motion.div
            key={`orbit-${o.size}`}
            style={{ width: o.size, height: o.size }}
            className="absolute"
            animate={{ rotate: 360 * o.direction }}
            transition={{ duration: o.duration, repeat: Infinity, ease: "linear" }}
          >
            <span
              className={`absolute left-1/2 top-0 h-1.5 w-1.5 -translate-x-1/2 rounded-full ${o.dot} shadow-aiGlow`}
            />
          </motion.div>
        ))}

      {/* slow scanning sweep near the core — "always processing" */}
      <motion.div
        animate={reducedMotion.current ? {} : { rotate: 360 }}
        transition={{ duration: 6, repeat: Infinity, ease: "linear" }}
        className="absolute h-24 w-24 rounded-full opacity-40"
        style={{
          background:
            "conic-gradient(from 0deg, transparent 0%, rgba(108,123,240,0.55) 12%, transparent 28%)",
        }}
      />

      {/* core */}
      <div className="relative h-16 w-16 rounded-full border border-white/10 bg-tracePanel/90 shadow-aiGlow backdrop-blur-glass">
        <motion.div
          className="absolute inset-0 rounded-full bg-ai/25"
          animate={{ opacity: [0.35, 0.65, 0.35], scale: [1, 1.06, 1] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>

    </div>
  );
}