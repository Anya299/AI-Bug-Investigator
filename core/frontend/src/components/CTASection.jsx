import Reveal from "./Reveal";

export default function CTASection({ onStartInvestigation }) {
  return (
    <section className="mx-auto max-w-3xl px-6 py-32 text-center">
      <Reveal>
        <h2 className="font-display text-4xl font-bold tracking-tight text-textPrimary sm:text-5xl">
          Start investigating.
        </h2>
        <p className="mt-4 text-textSecondary">
          Free to try. No setup.
        </p>
        <button
          onClick={onStartInvestigation}
          className="mt-10 rounded-xl border border-cyan/40 bg-cyan/10 px-8 py-4 font-mono text-sm text-cyan backdrop-blur-glass transition hover:bg-cyan/20"
        >
          Start Investigation →
        </button>
      </Reveal>
    </section>
  );
}