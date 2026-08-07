import BugForm from "./BugForm";
import GlassCard from "./ui/GlassCard";
import AIStatus from "./ui/AIStatus";

// Only "Investigate" is real right now. The rest are shown so the
// information architecture reads correctly, not because they're wired
// to real data yet — marked "soon" rather than pretending otherwise.
const NAV_ITEMS = [
  { label: "Investigate", active: true },
  { label: "History" },
  { label: "Knowledge Base" },
  { label: "Settings" },
];

export default function InvestigationWorkspace({
  apiBaseUrl,
  authToken,
  authError,
  onBackToHome,
}) {
  return (
    <div className="flex min-h-screen bg-traceBg text-textPrimary">

      <aside className="hidden w-60 shrink-0 flex-col border-r border-line/60 bg-tracePanel/40 backdrop-blur-glass sm:flex">

        <button
          onClick={onBackToHome}
          className="flex items-center gap-2 px-6 py-6 text-left transition-opacity hover:opacity-80"
        >
          <span className="h-2 w-2 rounded-full bg-cyan" />
          <span className="font-display text-sm font-bold tracking-tight">trace</span>
        </button>

        <nav className="flex-1 space-y-1 px-3">
          {NAV_ITEMS.map((item) => (
            <div
              key={item.label}
              className={`rounded-lg px-3 py-2 font-mono text-xs ${
                item.active ? "bg-cyan/10 text-cyan" : "text-textDim"
              }`}
            >
              {item.label}
              {!item.active && (
                <span className="ml-2 text-[10px] text-textDim/60">soon</span>
              )}
            </div>
          ))}
        </nav>

      </aside>

      <div className="flex-1">

        <header className="flex items-center justify-between border-b border-line/60 bg-tracePanel/30 px-6 py-4 backdrop-blur-glass sm:px-10">
          <button
            onClick={onBackToHome}
            className="font-mono text-xs text-textSecondary transition-colors hover:text-cyan"
          >
            ← Home
          </button>
          <AIStatus />
        </header>

        <main className="mx-auto max-w-6xl px-6 py-12 sm:px-10">

          <div className="mb-8">
            <h1 className="text-3xl font-bold">Investigation Workspace</h1>
            <p className="mt-2 text-textSecondary">
              Paste evidence. Let Trace find the root cause.
            </p>
          </div>

          {authError && (
            <p className="mb-4 font-mono text-sm text-redAccent">{authError}</p>
          )}

          <GlassCard className="trace-hover-lift p-6 sm:p-10">
            <BugForm apiBaseUrl={apiBaseUrl} authToken={authToken} />
          </GlassCard>

        </main>

      </div>

    </div>
  );
}