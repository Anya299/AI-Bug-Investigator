import { useEffect, useState } from "react";

const TRACE_LINES = [
  { text: "$ analyzing traceback...", color: "text-textSecondary", delay: 0 },
  {
    text: "File \"app/routes/orders.py\", line 84, in create_order",
    color: "text-textPrimary",
    delay: 400,
  },
  {
    text: "KeyError: 'customer_id' not found in payload",
    color: "text-redAccent",
    delay: 800,
  },
  { text: "", color: "", delay: 200 },
  {
    text: "root cause  →  request schema allows missing customer_id,",
    color: "text-cyan",
    delay: 500,
  },
  {
    text: "              validation only runs after DB write attempt",
    color: "text-cyan",
    delay: 200,
  },
  { text: "confidence  →  87%", color: "text-amber", delay: 400 },
  {
    text: "fix         →  move Pydantic validation before order.create()",
    color: "text-textPrimary",
    delay: 500,
  },
];

export default function TraceHero() {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    if (visibleCount >= TRACE_LINES.length) return;
    const delay = TRACE_LINES[visibleCount].delay;
    const timer = setTimeout(() => setVisibleCount((c) => c + 1), delay);
    return () => clearTimeout(timer);
  }, [visibleCount]);

  return (
    <div className="relative rounded-lg border border-line bg-surface shadow-2xl shadow-black/40 overflow-hidden">
      <div className="flex items-center gap-2 border-b border-line px-4 py-3">
        <span className="h-2.5 w-2.5 rounded-full bg-redAccent/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-amber/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-cyan/70" />
        <span className="ml-3 font-mono text-xs text-textDim">
          trace — investigation.log
        </span>
      </div>

      <div className="p-6 font-mono text-[13px] leading-relaxed sm:text-sm">
        {TRACE_LINES.slice(0, visibleCount).map((line, i) => (
          <div
            key={i}
            className={`${line.color} ${
              i === visibleCount - 1 ? "trace-cursor" : ""
            } whitespace-pre-wrap`}
          >
            {line.text || "\u00A0"}
          </div>
        ))}
      </div>
    </div>
  );
}