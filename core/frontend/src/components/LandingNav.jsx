import { motion } from "framer-motion";

export default function LandingNav({ onStartInvestigation }) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="fixed inset-x-0 top-0 z-50 border-b border-line/40 bg-traceBg/40 backdrop-blur-xl"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <span className="font-display text-lg font-bold tracking-tight text-textPrimary">
          trace
        </span>

        <button
          onClick={onStartInvestigation}
          className="rounded-lg border border-cyan/40 bg-cyan/10 px-4 py-2 font-mono text-xs text-cyan transition hover:bg-cyan/20"
        >
          Start Investigation →
        </button>
      </div>
    </motion.header>
  );
}