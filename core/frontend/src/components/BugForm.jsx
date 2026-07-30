import { useState, useRef } from "react";
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
  const startTimeRef = useRef(null);

  const update = (field) => (e) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const handlePasteAutoFill = (e) => {
    const text = e.target.value;
    setForm((f) => autoFillFromRawText(text, f));
  };

  const isValid = form.stack_trace.trim().length > 5;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValid) return;

    setStatus("loading");
    setIsWakingUp(false);

    const wakeTimer = setTimeout(() => {
      setIsWakingUp(true);
    }, 4000);


    setErrorMessage("");
    setResult(null);
    setCopied(false);
    startTimeRef.current = performance.now();

    try {
      const res = await fetch(`${apiBaseUrl}/analyze-bug`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify({
          description:
            form.description ||
            form.stack_trace.split("\n").filter(Boolean).join(" ").slice(0, 500),
          stack_trace: form.stack_trace,
          language: form.language || null,
          severity: form.severity,
          mode, // "quick" lets the backend try a pattern-match shortcut first
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

      clearTimeout(wakeTimer);
      setIsWakingUp(false);

      setElapsedMs(Math.round(performance.now() - startTimeRef.current));
            setResult(finalResult);
            setStatus("success");

    } catch (err) {

      clearTimeout(wakeTimer);
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
    <div className="grid gap-8 lg:grid-cols-2 lg:gap-10">
      <form
        onSubmit={handleSubmit}
        className="space-y-5 rounded-lg border border-line bg-surface p-6 shadow-card"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-mono-display text-lg font-semibold text-textPrimary">
              Paste your error
            </h2>
            <p className="mt-1 text-sm text-textSecondary">
              Terminal output, stack trace, or a plain description — we'll
              fill in the rest.
            </p>
          </div>
          <ModeToggle mode={mode} setMode={setMode} />
        </div>

        <Field label="Error / terminal output">
          <textarea
            className={`${inputClasses} font-mono text-xs`}
            rows={7}
            placeholder={`Paste anything, e.g.:\n\nTraceback (most recent call last):\n  File "main.py", line 5\nModuleNotFoundError: No module named 'fastapi'`}
            value={form.stack_trace}
            onChange={handlePasteAutoFill}
            autoFocus
          />
        </Field>

        {(form.language || form.framework) && (
          <div className="flex flex-wrap gap-2">
            {form.language && <DetectedTag label={form.language} />}
            {form.framework && <DetectedTag label={form.framework} />}
          </div>
        )}

        <button
          type="button"
          onClick={() => setShowDetails((v) => !v)}
          className="font-mono text-xs text-textDim underline decoration-dotted underline-offset-4 hover:text-cyan"
        >
          {showDetails ? "hide extra context" : "+ add more context (optional, improves accuracy)"}
        </button>

        {showDetails && (
          <div className="space-y-4 border-t border-line pt-4">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Language">
                <select className={inputClasses} value={form.language} onChange={update("language")}>
                  <option value="">Auto-detect</option>
                  {LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
              </Field>
              <Field label="Framework">
                <select className={inputClasses} value={form.framework} onChange={update("framework")}>
                  <option value="">Auto-detect</option>
                  {FRAMEWORKS.map((f) => <option key={f} value={f}>{f}</option>)}
                </select>
              </Field>
            </div>
            <Field label="Environment" hint="OS, version, key dependencies">
              <input
                className={inputClasses}
                placeholder="e.g. Ubuntu 22.04, Python 3.11"
                value={form.environment}
                onChange={update("environment")}
              />
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Expected behavior">
                <input className={inputClasses} value={form.expected_behavior} onChange={update("expected_behavior")} />
              </Field>
              <Field label="Actual behavior">
                <input className={inputClasses} value={form.actual_behavior} onChange={update("actual_behavior")} />
              </Field>
            </div>
            <Field label="Reproduction steps">
              <textarea className={inputClasses} rows={2} value={form.reproduction_steps} onChange={update("reproduction_steps")} />
            </Field>
            <Field label="Severity">
              <select className={inputClasses} value={form.severity} onChange={update("severity")}>
                {SEVERITIES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </Field>
          </div>
        )}

        <button
          type="submit"
          disabled={!isValid || status === "loading"}
          className="w-full rounded-md bg-amber px-4 py-3 font-mono-display text-sm font-semibold text-ink shadow-glowAmber transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40 disabled:shadow-none"
        >
          {status === "loading"
            ? mode === "quick" ? "Fixing…" : "Investigating…"
            : mode === "quick" ? "Get instant fix" : "Run full investigation"}
        </button>

        {status === "loading" && isWakingUp && (
          <div className="rounded-md border border-cyan/30 bg-cyan/10 p-4">
            <p className="font-mono text-sm text-cyan">
              🚀 Warming up the analysis engine...
           </p>

            <p className="mt-2 text-xs text-textSecondary">
              This is the first request, so the AI service may take 30–60 seconds to start.
              Once it's awake, future analyses will be much faster.
           </p>
         </div>
       )}

        {status === "error" && <p className="text-sm text-redAccent">{errorMessage}</p>}
      </form>

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

function DetectedTag({ label }) {
  return (
    <span className="rounded-full border border-cyan/30 bg-cyan/10 px-2.5 py-1 font-mono text-xs text-cyan">
      detected: {label}
    </span>
  );
}