import { useState, useRef, useEffect } from "react";
import ResultPanel from "./ResultPanel";

const LANGUAGES = ["Python", "JavaScript/TypeScript", "Java", "Go", "Other"];
const FRAMEWORKS = ["FastAPI", "Django", "Flask", "React", "Node/Express", "Other"];
const SEVERITIES = [
  { value: "low", label: "Low — annoying, not blocking" },
  { value: "medium", label: "Medium — slows down work" },
  { value: "high", label: "High — blocking a feature" },
  { value: "critical", label: "Critical — production is broken" },
];

const initialState = {
  language: "",
  framework: "",
  environment: "",
  description: "",
  stack_trace: "",
  reproduction_steps: "",
  expected_behavior: "",
  actual_behavior: "",
  severity: "medium",
};

// The three checkpoints Trace visibly works through while it investigates.
// Shown one at a time so "analyzing" reads as real progress, not a spinner.
const INVESTIGATION_STEPS = [
  "Reading logs",
  "Finding root cause",
  "Generating fix",
];

function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-textPrimary">{label}</span>
      {hint && <span className="ml-2 text-xs text-textDim">{hint}</span>}
      <div className="mt-1.5">{children}</div>
    </label>
  );
}

const inputClasses =
  "w-full rounded-md border border-line bg-ink px-3 py-2.5 text-sm text-textPrimary placeholder:text-textDim focus:border-cyan focus:outline-none transition-colors";

// Extracts language / framework / a one-line description straight out of a
// raw paste — this is what makes "paste anything and go" feel instant,
// instead of asking the user to hand-fill fields first.
function autoFillFromRawText(text, existing) {
  const next = { ...existing, stack_trace: text };
  const lower = text.toLowerCase();

  if (!existing.language) {
    if (lower.includes("traceback (most recent call last)") || /\.py["):]/.test(lower)) {
      next.language = "Python";
    } else if (lower.includes("node_modules") || /\.js:\d+/.test(lower) || lower.includes("at object.")) {
      next.language = "JavaScript/TypeScript";
    } else if (lower.includes("exception in thread")) {
      next.language = "Java";
    }
  }

  if (!existing.framework) {
    if (lower.includes("fastapi")) next.framework = "FastAPI";
    else if (lower.includes("django")) next.framework = "Django";
    else if (lower.includes("flask")) next.framework = "Flask";
    else if (lower.includes("react")) next.framework = "React";
  }

  if (!existing.description) {
    // The last non-empty line of a traceback is almost always the actual
    // error message — e.g. "ModuleNotFoundError: No module named 'fastapi'".
    const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
    if (lines.length > 0) next.description = lines[lines.length - 1];
  }

  return next;
}

// One case number per mount — gives the panel an identity instead of being
// an anonymous form. Format echoes the product name: TR-####.
function generateCaseId() {
  return `TR-${Math.floor(1000 + Math.random() * 9000)}`;
}

export default function BugForm({ apiBaseUrl = "", authToken = "" }) {
  const [form, setForm] = useState(initialState);
  const [mode, setMode] = useState("quick"); // "quick" | "full"
  const [showDetails, setShowDetails] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [isWakingUp, setIsWakingUp] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [elapsedMs, setElapsedMs] = useState(null);
  const [copied, setCopied] = useState(false);
  const [caseId] = useState(generateCaseId);
  const [completedSteps, setCompletedSteps] = useState(0);
  const startTimeRef = useRef(null);
  const stepTimerRef = useRef(null);

  const update = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const handlePasteAutoFill = (e) => {
    const text = e.target.value;
    setForm((f) => autoFillFromRawText(text, f));
  };

  const isValid = form.stack_trace.trim().length > 5;

  // Advances INVESTIGATION_STEPS one at a time while status === "loading".
  // Caps at the second-to-last step so it never claims "done" before the
  // real response lands — the final step only completes on actual success.
  useEffect(() => {
    if (status !== "loading") {
      clearInterval(stepTimerRef.current);
      return;
    }
    setCompletedSteps(0);
    stepTimerRef.current = setInterval(() => {
      setCompletedSteps((n) => Math.min(n + 1, INVESTIGATION_STEPS.length - 1));
    }, 1100);
    return () => clearInterval(stepTimerRef.current);
  }, [status]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid) return;

    setStatus("loading");
    setIsWakingUp(false);
    setErrorMessage("");
    setResult(null);
    setCopied(false);
    startTimeRef.current = performance.now();

    // Free-tier Render instances spin down when idle, so a genuinely cold
    // first request can take 30-60s. Past 5s of waiting, swap in a message
    // that names that reality so it reads as expected, not broken.
    const wakeupTimer = setTimeout(() => {
      setIsWakingUp(true);
    }, 5000);

    try {
      const res = await fetch(`${apiBaseUrl}/analyze-bug`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify({
          project_id: 1,
          description:
            form.description?.trim() ||
            form.stack_trace?.trim().split("\n").filter(Boolean).join(" ").slice(0, 500) ||
            "Unknown bug report",

          stack_trace: form.stack_trace || null,
          language: form.language || null,
          severity: form.severity || "medium",
          mode: mode === "full" ? "full" : "quick",
          framework: form.framework || null,
          environment: form.environment || null,
          reproduction_steps: form.reproduction_steps || null,
          expected_behavior: form.expected_behavior || null,
          actual_behavior: form.actual_behavior || null,
       }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }

      const finalResult = await res.json();

      clearTimeout(wakeupTimer);
      setIsWakingUp(false);
      setCompletedSteps(INVESTIGATION_STEPS.length);

      setElapsedMs(Math.round(performance.now() - startTimeRef.current));
      setResult(finalResult);
      setStatus("success");
    } catch (err) {
      clearTimeout(wakeupTimer);
      setIsWakingUp(false);

      setErrorMessage(err.message || "Something went wrong. Try again.");
      setStatus("error");
    }
  };

  const handleCopyFix = () => {
    if (!result?.fix_recommendation) return;
    navigator.clipboard.writeText(result.fix_recommendation);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
  <div className="grid gap-8 lg:grid-cols-2">

    {/* Local keyframes — scoped here so this component stays self-contained
        and doesn't require touching tailwind.config for one-off motion. */}
    <style>{`
      @keyframes traceFadeInUp {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @keyframes traceBlink {
        0%, 45% { opacity: 1; }
        50%, 95% { opacity: 0; }
        100% { opacity: 1; }
      }
      @keyframes traceCheckPop {
        0%   { transform: scale(0.6); opacity: 0; }
        60%  { transform: scale(1.15); opacity: 1; }
        100% { transform: scale(1); opacity: 1; }
      }
      .trace-fade-in { animation: traceFadeInUp 0.35s ease-out both; }
      .trace-cursor::after {
        content: "";
        display: inline-block;
        width: 6px;
        height: 1em;
        margin-left: 2px;
        vertical-align: -0.15em;
        background: currentColor;
        animation: traceBlink 1.1s step-end infinite;
      }
      .trace-check-pop { animation: traceCheckPop 0.3s ease-out both; }
      @media (prefers-reduced-motion: reduce) {
        .trace-fade-in, .trace-check-pop { animation: none; }
        .trace-cursor::after { animation: none; opacity: 1; }
      }
    `}</style>

    {/* LEFT: Investigation Input */}

    <form
      onSubmit={handleSubmit}
      className="
      rounded-3xl
      border
      border-white/10
      bg-tracePanel/80
      backdrop-blur-xl
      shadow-glass
      p-6
      space-y-6
      "
    >


      <div className="flex items-start justify-between">

        <div>

          <div className="flex items-center gap-2">
            <p
              className="
              font-mono
              text-xs
              text-ai
              tracking-widest
              "
            >
              EVIDENCE COLLECTOR
            </p>

            <span className="h-1 w-1 rounded-full bg-textDim" />

            <p className="font-mono text-xs text-textDim tracking-widest">
              CASE #{caseId} · OPEN
            </p>
          </div>


          <h2
            className="
            mt-2
            text-2xl
            font-semibold
            "
          >
            Paste your bug
          </h2>


          <p
            className="
            mt-2
            text-sm
            text-textSecondary
            "
          >
            Trace automatically detects your stack and investigates.
          </p>

        </div>


        <ModeToggle
          mode={mode}
          setMode={setMode}
        />

      </div>



      {/* Editor */}

      <div
        className="
        rounded-2xl
        border
        border-white/10
        bg-black/30
        overflow-hidden
        transition-colors
        focus-within:border-ai/40
        "
      >

        <div
          className="
          flex
          items-center
          gap-2
          border-b
          border-white/10
          px-4
          py-3
          "
        >

          <span className="h-3 w-3 rounded-full bg-redAccent"/>
          <span className="h-3 w-3 rounded-full bg-amber"/>
          <span className="h-3 w-3 rounded-full bg-ai"/>


          <span
            className="
            ml-3
            font-mono
            text-xs
            text-textDim
            "
          >
            error.log
          </span>

        </div>



        <textarea

          id="stack_trace"
          name="stack_trace"

          className="
          min-h-[260px]
          w-full
          resize-none
          bg-transparent
          p-5
          font-mono
          text-sm
          leading-relaxed
          text-textPrimary
          outline-none
          placeholder:text-textDim
          "

          placeholder={`Paste stack trace...

Example:

Traceback:
File "main.py"
ModuleNotFoundError
`}
          value={form.stack_trace}

          onChange={handlePasteAutoFill}

          autoFocus

        />


      </div>




      {/* Detection */}

      {(form.language || form.framework) && (

        <div className="trace-fade-in">

          <p className="mb-3 text-xs text-textSecondary">
            DETECTED STACK
          </p>


          <div className="flex flex-wrap gap-2">

            {form.language &&
              <DetectedTag label={form.language} delay={0}/>
            }


            {form.framework &&
              <DetectedTag label={form.framework} delay={80}/>
            }

          </div>


        </div>

      )}






      <button

        type="button"

        onClick={() => setShowDetails(v=>!v)}

        className="
        font-mono
        text-xs
        text-textSecondary
        hover:text-ai
        transition-colors
        "

      >

        {showDetails
          ? "− hide advanced context"
          : "+ add environment context"
        }

      </button>





      {showDetails && (

        <div
          className="
          trace-fade-in
          space-y-4
          border-t
          border-white/10
          pt-5
          "
        >

          <Field label="Environment">

            <input

              className={inputClasses}

              placeholder="Python 3.11, Ubuntu, Redis..."

              value={form.environment}

              onChange={update("environment")}

            />

          </Field>


          <Field label="Reproduction steps">

            <textarea

              className={inputClasses}

              rows={3}

              value={form.reproduction_steps}

              onChange={update("reproduction_steps")}

            />

          </Field>


        </div>

      )}







      <button

        disabled={!isValid || status==="loading"}

        className="
        w-full
        rounded-xl
        bg-ai
        py-4
        font-mono
        font-semibold
        text-black
        shadow-aiGlow
        transition
        hover:scale-[1.02]
        active:scale-[0.99]
        disabled:opacity-40
        disabled:hover:scale-100
        "

      >

        {status==="loading"
          ? "AI ENGINE ANALYZING..."
          : "START INVESTIGATION →"
        }


      </button>




      {status==="loading" && (

        <div
          className="
          trace-fade-in
          rounded-xl
          border
          border-ai/20
          bg-aiSoft
          p-4
          font-mono
          text-sm
          text-ai
          space-y-1.5
          "
        >

          {INVESTIGATION_STEPS.map((step, i) => {
            const done = i < completedSteps;
            const active = i === completedSteps;
            return (
              <div key={step} className="flex items-center gap-2">
                <span className={done ? "trace-check-pop" : ""}>
                  {done ? "✓" : "●"}
                </span>
                <span className={active ? "trace-cursor" : ""}>
                  {step}
                  {done ? "" : active ? "" : "…"}
                </span>
              </div>
            );
          })}

          {isWakingUp && (
            <p className="mt-2 text-xs text-textDim">
              First request can take up to a minute — waking the server.
            </p>
          )}

        </div>

      )}





      {status==="error" && (

        <div
          className="
          trace-fade-in
          rounded-xl
          border
          border-redAccent/30
          bg-redAccent/10
          p-4
          "
        >
          <p className="font-mono text-xs text-redAccent tracking-widest">
            CASE #{caseId} · INVESTIGATION FAILED
          </p>
          <p className="mt-1 text-sm text-redAccent">
            {errorMessage}
          </p>
        </div>

      )}


    </form>




    {/* RIGHT */}

    <ResultPanel

      status={status}

      result={result}

      mode={mode}

      elapsedMs={elapsedMs}

      onCopyFix={handleCopyFix}

      copied={copied}

    />


  </div>
);
}

function ModeToggle({ mode, setMode }) {
  return (
    <div className="flex shrink-0 rounded-md border border-line bg-ink p-0.5 font-mono text-xs">
      {["quick", "full"].map((m) => (
        <button
          key={m}
          type="button"
          onClick={() => setMode(m)}
          className={`rounded px-3 py-1.5 transition-colors ${
            mode === m ? "bg-cyan text-ink font-semibold" : "text-textDim hover:text-textSecondary"
          }`}
        >
          {m === "quick" ? "Quick fix" : "Full investigation"}
        </button>
      ))}
    </div>
  );
}

function DetectedTag({ label, delay = 0 }) {
  return (
    <span
      style={{ animationDelay: `${delay}ms` }}
      className="trace-fade-in rounded-full border border-cyan/30 bg-cyan/10 px-2.5 py-1 font-mono text-xs text-cyan"
    >
      detected: {label}
    </span>
  );
}