import TraceHero from "./components/TraceHero";
import BugForm from "./components/BugForm";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

function App() {
  return (
    <div className="min-h-screen bg-ink">
      <Header />
      <Hero />

      <section id="investigate" className="mx-auto max-w-5xl px-6 py-16 sm:py-20">
        <BugForm
          apiBaseUrl={API_BASE_URL}
          authToken= "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJyYXlhcmlkYXJlQHRlc3QuY29tIiwiZXhwIjoxNzg1NDk1OTA1fQ.SnR8UIcXExOfcUVZbn2j0myrRKQExEVShwOTw-VP1-4"
        />
      </section>

      <Footer />
    </div>
  );
}

function Header() {
  return (
    <header className="border-b border-line/60">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-cyan" />
          <span className="font-mono-display text-sm font-bold tracking-tight text-textPrimary">
            trace
          </span>
        </div>

        <a
          href="#investigate"
          className="rounded-md border border-line px-4 py-2 font-mono text-xs text-textSecondary transition-colors hover:border-cyan hover:text-cyan"
        >
          Investigate a bug →
        </a>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="mx-auto grid max-w-6xl gap-12 px-6 py-16 sm:py-24 lg:grid-cols-2 lg:items-center lg:py-32">
      <div>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-cyan">
          for python · fastapi · django
        </p>

        <h1 className="mt-4 font-mono-display text-4xl font-bold leading-[1.1] tracking-tight text-textPrimary sm:text-5xl">
          Stop guessing at
          <br />
          root causes.
        </h1>

        <p className="mt-5 max-w-md text-base leading-relaxed text-textSecondary">
          Paste a stack trace. Get a confidence-scored root cause, a
          step-by-step investigation, and a fix — grounded in the actual
          evidence in your error, not a generic guess.
        </p>

        <div className="mt-8 flex items-center gap-4">
          <a
            href="#investigate"
            className="rounded-md bg-amber px-5 py-3 font-mono-display text-sm font-semibold text-ink transition-opacity hover:opacity-90"
          >
            Investigate your first bug
          </a>

          <span className="font-mono text-xs text-textDim">
            no signup required to try
          </span>
        </div>
      </div>

      <TraceHero />
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-line/60">
      <div className="mx-auto max-w-6xl px-6 py-8">
        <p className="font-mono text-xs text-textDim">
          trace — built for developers who'd rather understand the bug than
          just paste it into a chat window.
        </p>
      </div>
    </footer>
  );
}

export default App;