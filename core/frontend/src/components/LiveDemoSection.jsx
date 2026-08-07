import Reveal from "./Reveal";
import TraceHero from "./TraceHero";

export default function LiveDemoSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-24 sm:py-32">

      <Reveal>
        <p className="font-mono text-xs uppercase tracking-[0.25em] text-textDim">
          Live investigation
        </p>
        <h2 className="mt-4 font-display text-3xl font-bold text-textPrimary sm:text-4xl">
          Watch it work.
        </h2>
      </Reveal>

      <Reveal delay={150}>
        <div className="mt-12">
          <TraceHero />
        </div>
      </Reveal>

    </section>
  );
}