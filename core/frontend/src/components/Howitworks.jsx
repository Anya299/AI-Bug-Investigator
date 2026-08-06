import Reveal from "./Reveal";

const STEPS = [
  {
    n: "01",
    title: "Paste the error",
    text: "Stack trace, log, or a one-line description — Trace detects your stack automatically.",
  },
  {
    n: "02",
    title: "Trace investigates",
    text: "It reads the evidence, checks known failure patterns, and finds the actual root cause.",
  },
  {
    n: "03",
    title: "Get the fix",
    text: "A confidence-scored report, the fix, and the reasoning behind it — not a guess.",
  },
];

export default function HowItWorks({ innerRef }) {
  return (
    <section
      ref={innerRef}
      id="how"
      className="flex h-screen snap-start snap-always items-center"
    >
      <div className="mx-auto w-full max-w-6xl px-6">

        <Reveal>
          <p className="font-mono text-xs uppercase tracking-[0.25em] text-textDim">
            How it works
          </p>
        </Reveal>

        <div className="mt-14 grid gap-10 sm:grid-cols-3 sm:gap-8">
          {STEPS.map((step, i) => (
            <Reveal key={step.n} delay={i * 120}>
              <div>
                <p className="font-mono text-sm text-ai">{step.n}</p>
                <h3 className="mt-3 text-xl font-semibold text-textPrimary">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-textSecondary">
                  {step.text}
                </p>
              </div>
            </Reveal>
          ))}
        </div>

      </div>
    </section>
  );
}