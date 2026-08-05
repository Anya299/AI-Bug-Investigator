import { useEffect, useMemo, useState } from "react";
import GlassCard from "./ui/GlassCard";
import AIStatus from "./ui/AIStatus";

const TRACE_LINES = [
  "trace.engine.boot()",
  "Loading investigation model...",
  "Reading stack evidence...",
  "Detected: FastAPI + Redis + PostgreSQL",
  "Searching previous failures...",
  "Root cause discovered",
  "Generating production fix..."
];

// The one line in the boot sequence that's actually the payoff — everything
// before it is setup. Marking it distinctly is what makes the terminal read
// as an investigation instead of a generic loading log.
const HIGHLIGHT_LINE = "Root cause discovered";

const FINAL_CONFIDENCE = 94;

export default function TraceHero() {

  const [lines, setLines] = useState([]);
  const [confidence, setConfidence] = useState(0);

  const done = lines.length >= TRACE_LINES.length;


  useEffect(() => {

    if (lines.length >= TRACE_LINES.length) return;


    const timer = setTimeout(() => {

      setLines((previous) => [
        ...previous,
        TRACE_LINES[previous.length]
      ]);

    }, 700);


    return () => clearTimeout(timer);

  }, [lines]);


  // Counts the confidence score up once the sequence finishes, instead of
  // showing a static 94% the whole time — the number becomes evidence that
  // something just resolved, not decoration sitting there from page load.
  useEffect(() => {

    if (!done) return;

    const prefersReducedMotion =
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

    if (prefersReducedMotion) {
      setConfidence(FINAL_CONFIDENCE);
      return;
    }

    const step = setInterval(() => {
      setConfidence((c) => {
        if (c >= FINAL_CONFIDENCE) {
          clearInterval(step);
          return FINAL_CONFIDENCE;
        }
        return c + 2;
      });
    }, 25);

    return () => clearInterval(step);

  }, [done]);


  const statusLabel = useMemo(() => {
    if (done) return "ROOT CAUSE FOUND";
    if (lines.length === 0) return "BOOTING";
    return "ANALYZING";
  }, [done, lines.length]);


  return (

    <div className="relative">

      {/* AI glow background */}
      <div
        className="
        absolute
        -inset-20
        rounded-full
        bg-ai/10
        blur-3xl
        "
      />

      <style>{`
        @keyframes traceStampIn {
          0%   { transform: scale(1.6) rotate(-6deg); opacity: 0; }
          55%  { transform: scale(0.92) rotate(-6deg); opacity: 1; }
          100% { transform: scale(1) rotate(-6deg); opacity: 1; }
        }
        .trace-stamp-in { animation: traceStampIn 0.4s ease-out both; }
        @keyframes traceLineMark {
          from { background-size: 0% 100%; }
          to   { background-size: 100% 100%; }
        }
        .trace-line-mark {
          background-image: linear-gradient(transparent 65%, var(--tw-mark-color, rgba(242,169,59,0.35)) 65%);
          background-repeat: no-repeat;
          animation: traceLineMark 0.5s ease-out 0.15s both;
        }
        @media (prefers-reduced-motion: reduce) {
          .trace-stamp-in { animation: none; }
          .trace-line-mark { animation: none; background-size: 100% 100%; }
        }
      `}</style>


      <GlassCard
        className="
        trace-hover-lift
        relative
        overflow-hidden
        p-0
        "
      >


        {/* Header */}

        <div
          className="
          flex
          items-center
          justify-between
          border-b
          border-white/10
          px-6
          py-5
          "
        >

          <div>

            <p
              className="
              font-mono
              text-xs
              tracking-widest
              text-textSecondary
              "
            >
              TRACE AI CORE
            </p>


            <h3
              className="
              mt-1
              text-xl
              font-semibold
              text-textPrimary
              "
            >
              Autonomous Debugging Engine
            </h3>

          </div>


          <div className="flex items-center gap-3">

            {done && (
              <div
                className="
                trace-stamp-in
                trace-rotated-badge
                pointer-events-none
                select-none
                rounded-lg
                border-2
                border-dashed
                border-ai/60
                bg-aiSoft
                px-2.5
                py-1
                -rotate-6
                "
              >
                <span className="font-mono text-[10px] tracking-widest font-bold text-ai">
                  CASE CONFIRMED
                </span>
              </div>
            )}

            <AIStatus />

          </div>

        </div>



        {/* Intelligence cards */}

        <div
          className="
          grid
          grid-cols-3
          gap-3
          p-6
          "
        >

          <div
            className="
            rounded-xl
            border
            border-white/10
            bg-white/5
            p-4
            "
          >

            <p className="text-xs text-textSecondary">
              MODEL
            </p>

            <p
              className="
              mt-2
              font-mono
              text-ai
              "
            >
              Claude Reasoning
            </p>

          </div>



          <div
            className="
            rounded-xl
            border
            border-white/10
            bg-white/5
            p-4
            transition-colors
            "
          >

            <p className="text-xs text-textSecondary">
              STATUS
            </p>

            <p
              className={`
              mt-2
              font-mono
              transition-colors
              ${done ? "text-ai" : "text-textPrimary"}
              `}
            >
              {statusLabel}
            </p>

          </div>




          <div
            className="
            rounded-xl
            border
            border-white/10
            bg-white/5
            p-4
            "
          >

            <p className="text-xs text-textSecondary">
              CONFIDENCE
            </p>

            <p
              className="
              mt-2
              font-mono
              text-amber
              tabular-nums
              "
            >
              {confidence}%
            </p>

          </div>


        </div>




        {/* Terminal */}

        <div
          className="
          mx-6
          mb-6
          rounded-2xl
          border
          border-white/10
          bg-black/30
          p-5
          font-mono
          text-sm
          "
        >


          {lines.map((line, index) => {

            const isHighlight = line === HIGHLIGHT_LINE;

            return (

              <div
                key={index}
                className="
                mb-3
                animate-fadeUp
                "
              >

                <span
                  className={isHighlight ? "text-amber" : "text-ai"}
                >
                  $
                </span>


                <span
                  className={`
                  ml-3
                  ${isHighlight
                    ? "trace-line-mark font-semibold text-textPrimary"
                    : "text-textPrimary"}
                  `}
                >
                  {line}
                </span>


              </div>

            );

          })}



          {lines.length < TRACE_LINES.length && (

            <span
              className="
              text-ai
              animate-pulse
              "
            >
              ▊
            </span>

          )}


        </div>




        {/* Footer */}

        <div
          className="
          flex
          justify-between
          border-t
          border-white/10
          px-6
          py-4
          font-mono
          text-xs
          text-textDim
          "
        >

          <span>
            Evidence collector active
          </span>


          <span>
            {done ? "Root cause engine ready · fix generated" : "Root cause engine ready"}
          </span>


        </div>


      </GlassCard>


    </div>

  );
}