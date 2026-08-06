import { motion } from "framer-motion";
import AICore from "./AICore";

const HEADLINE = ["Trace.", "Analyze.", "Resolve."];

const container = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.08, delayChildren: 0.1 },
  },
};

const word = {
  hidden: { opacity: 0, y: 16, filter: "blur(6px)" },
  show: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] },
  },
};

/**
 * onStartInvestigation is called, not navigated to directly — this lets
 * the parent play a real transition into the workspace instead of a
 * hard route change, once that piece is built next.
 */
export default function LandingHero({ onStartInvestigation }) {
  return (
    <section className="relative flex min-h-screen items-center justify-center px-6 pt-24">
      <div className="mx-auto grid w-full max-w-6xl items-center gap-16 lg:grid-cols-2">

        <div>
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="font-mono text-xs uppercase tracking-[0.3em] text-textDim"
          >
            AI Bug Investigator
          </motion.p>

          <motion.h1
            variants={container}
            initial="hidden"
            animate="show"
            className="mt-6 font-display text-6xl font-bold leading-[1.02] tracking-tight text-textPrimary sm:text-7xl lg:text-8xl"
          >
            {HEADLINE.map((w) => (
              <motion.span key={w} variants={word} className="block">
                {w}
              </motion.span>
            ))}
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.55 }}
            className="mt-8 max-w-md text-lg text-textSecondary"
          >
            Find root cause. Instantly.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.7 }}
            className="mt-10 flex flex-wrap items-center gap-4"
          >
            <button
              onClick={onStartInvestigation}
              className="rounded-xl border border-cyan/40 bg-cyan/10 px-7 py-3.5 font-mono text-sm text-cyan backdrop-blur-glass transition hover:bg-cyan/20"
            >
              Start Investigation →
            </button>

            <button className="rounded-xl border border-line px-7 py-3.5 font-mono text-sm text-textSecondary backdrop-blur-glass transition hover:border-cyan hover:text-cyan">
              Watch Demo
            </button>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.92 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          className="flex justify-center"
        >
          <AICore />
        </motion.div>

      </div>
    </section>
  );
}