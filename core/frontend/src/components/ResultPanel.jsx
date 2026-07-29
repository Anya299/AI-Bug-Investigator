import { useEffect, useState } from "react";

// Mirrors what analyze-bug actually does server-side: cache check, then
// pattern match, then (if needed) the LLM call, then the quality guard
// retry path. Timed to roughly typical latency since there's no SSE to
// drive this off real progress.
const LOADING_STAGES = [
  { label: "Checking cache…", ms: 0 },
  { label: "Matching known bug patterns…", ms: 550 },
  { label: "Building investigation report…", ms: 1400 },
  { label: "Validating output quality…", ms: 2600 },
];

function useLoadingStage(active) {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      setStageIndex(0);
      return;
    }
    const timers = LOADING_STAGES.slice(1).map((stage, i) =>
      setTimeout(() => setStageIndex(i + 1), stage.ms)
    );
    return () => timers.forEach(clearTimeout);
  }, [active]);

  return LOADING_STAGES[stageIndex].label;
}

function confidenceTier(score) {
  if (score >= 80) return { color: "#39d9c5", label: "high" };
  if (score >= 50) return { color: "#ffb454", label: "moderate" };
  return { color: "#ff6b6b", label: "low" };
}

function ConfidenceRing({ score = 0, size = 56 }) {
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(Math.max(score, 0), 100) / 100) * circumference;
  const { color, label } = confidenceTier(score);

  return (
    <div className="flex items-center gap-2.5" title={`${label} confidence`}>
      <svg width={size} height={size} viewBox="0 0 56 56" className="shrink-0">
        <circle cx="28" cy="28" r={radius} fill="none" stroke="var(--line)" strokeWidth="5" />
        <circle
          cx="28"
          cy="28"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="confidence-ring-fg"
        />
        <text
          x="28"
          y="32"
          textAnchor="middle"
          className="font-mono-display"
          fontSize="13"
          fontWeight="600"
          fill={color}
        >
          {score}
        </text>
      </svg>
      <div className="leading-tight">
        <p className="font-mono text-xs uppercase tracking-wide text-textDim">Confidence</p>
        <p className="font-mono text-xs font-semibold" style={{ color }}>
          {label}
        </p>
      </div>
    </div>
  );
}

function SourceBadge({ source }) {
  if (source === "pattern_match") {
    return (
      <span className="rounded-full border border-cyan/30 bg-cyan/10 px-2.5 py-1 font-mono text-xs text-cyan">
        ⚡ instant · known pattern
      </span>
    );
  }
  if (source === "cache") {
    return (
      <span className="rounded-full border border-line bg-ink px-2.5 py-1 font-mono text-xs text-textDim">
        from cache
      </span>
    );
  }
  return (
    <span className="rounded-full border border-line bg-ink px-2.5 py-1 font-mono text-xs text-textDim">
      full investigation
    </span>
  );
}

function ReportSection({ label, value, accent }) {
  if (!value) return null;
  const accentClass = accent === "cyan" ? "text-cyan" : "text-textPrimary";
  return (
    <div>
      <p className="font-mono text-xs uppercase tracking-wide text-textDim">{label}</p>
      <p className={`mt-1 whitespace-pre-wrap text-sm ${accentClass}`}>{value}</p>
    </div>
  );
}

export default function ResultPanel({ status, result, mode, elapsedMs, onCopyFix, copied }) {
  const stageLabel = useLoadingStage(status === "loading");

  if (status === "idle") {
    return (
      <div className="flex min-h-[300px] items-center justify-center rounded-lg border border-dashed border-line bg-surface/40 p-8 text-center">
        <p className="max-w-xs text-sm text-textDim">
          Drop a stack trace, terminal error, or bug description.
          Trace will investigate the evidence, find likely causes,
          and suggest the next fix.
      </p>
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div className="flex min-h-[300px] flex-col justify-center gap-4 rounded-lg border border-line bg-surface p-8 shadow-card">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-cyan" />
          <p key={stageLabel} className="animate-fadeUp font-mono text-sm text-textSecondary">
            {stageLabel}
          </p>
        </div>
        <div className="space-y-2">
          <div className="skeleton-shimmer h-3 w-4/5 animate-shimmer rounded" />
          <div className="skeleton-shimmer h-3 w-full animate-shimmer rounded" />
          <div className="skeleton-shimmer h-3 w-3/5 animate-shimmer rounded" />
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="rounded-lg border border-redAccent/30 bg-redAccent/5 p-6">
        <p className="font-mono-display text-sm font-semibold text-redAccent">
          Trace couldn't complete this investigation
       </p>

       <p className="mt-2 text-sm text-textSecondary">
         Retry once. If the issue continues, the bug report itself is useful —
         share the trace and help improve future investigations.
       </p>
    </div>
    );
  }

  if (!result) return null;

  return (
    <div className="animate-fadeUp space-y-4 rounded-lg border border-line bg-surface p-6 shadow-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-mono-display text-lg font-semibold text-textPrimary">
            {mode === "quick" ? "Instant fix" : "Investigation report"}
          </h3>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <SourceBadge source={result.source} />
            {elapsedMs != null && (
              <span className="rounded-full border border-line bg-ink px-2.5 py-1 font-mono text-xs text-textDim">
                {(elapsedMs / 1000).toFixed(1)}s
              </span>
            )}
          </div>
        </div>
        <ConfidenceRing score={result.confidence_score ?? 0} />
      </div>

      {/* Fix is always the top-line, most prominent thing regardless of mode. */}
      <div className="rounded-md border border-cyan/20 bg-cyan/5 p-4 shadow-glowCyan">
        <p className="font-mono text-xs uppercase tracking-wide text-textDim">Fix</p>
        <p className="mt-1 whitespace-pre-wrap font-mono text-sm text-cyan">
          {result.fix_recommendation}
        </p>
        <button
          type="button"
          onClick={onCopyFix}
          className="mt-3 rounded-md border border-line px-3 py-1.5 font-mono text-xs text-textSecondary transition-colors hover:border-cyan hover:text-cyan"
        >
          {copied ? "Copied ✓" : "Copy fix"}
        </button>
      </div>

      {result.bug_summary && (
        <ReportSection label="What's happening" value={result.bug_summary} />
      )}

      {(result.root_cause || result.investigation_steps?.length > 0) && (
        <details open={mode === "full"} className="group">
          <summary className="cursor-pointer list-none font-mono text-xs uppercase tracking-wide text-textDim hover:text-cyan">
            {mode === "quick" ? "▸ show reasoning + investigation" : "Investigation details"}
          </summary>
          <div className="mt-3 space-y-3 border-l border-line pl-4">
            <ReportSection label="Root cause" value={result.root_cause} accent="cyan" />

            {result.investigation_steps?.length > 0 && (
              <div>
                <p className="font-mono text-xs uppercase tracking-wide text-textDim">Investigation steps</p>
                <ol className="mt-2 space-y-1.5">
                  {result.investigation_steps.map((step, i) => (
                    <li key={i} className="flex gap-2 text-sm text-textSecondary">
                      <span className="font-mono text-cyan">{i + 1}.</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {result.evidence?.length > 0 && (
              <div>
                <p className="font-mono text-xs uppercase tracking-wide text-textDim">Evidence</p>
                <ul className="mt-2 space-y-1.5 border-l border-line/70 pl-3">
                  {result.evidence.map((item, i) => (
                    <li key={i} className="text-sm text-textSecondary">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.prevention && <ReportSection label="Prevention" value={result.prevention} />}
          </div>
        </details>
      )}

      <div className="flex items-center justify-between gap-2 border-t border-line pt-3">
        <button
          type="button"
          onClick={() => navigator.clipboard.writeText(JSON.stringify(result, null, 2))}
          className="flex-1 rounded-md border border-line px-4 py-2 font-mono text-xs text-textSecondary transition-colors hover:border-cyan hover:text-cyan"
        >
          Copy full report
        </button>
        {result.prompt_version && (
          <span className="shrink-0 font-mono text-[11px] text-textDim">
            v{result.prompt_version}
          </span>
        )}
      </div>
    </div>
  );
}