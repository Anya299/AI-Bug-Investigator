import Reveal from "./Reveal";

const STEPS = [
  {
    n: "01",
    title: "Paste the error",
    text: "Trace detects your stack automatically.",
  },
  {
    n: "02",
    title: "Trace investigates",
    text: "Evidence, patterns, root cause.",
  },
  {
    n: "03",
    title: "Get the fix",
    text: "Confidence-scored. Not a guess.",
  },
];

export default function HowItWorks() {
  return (
    <section className="mx-auto flex min-h-screen max-w-6xl items-center px-6 py-24">
      <div className="w-full">

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