import { useEffect, useState } from "react";
import TraceHero from "./components/TraceHero";
import BugForm from "./components/BugForm";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "https://ai-bug-investigator-9.onrender.com";

/**
 * Provisions an invisible guest account on first visit and stores the
 * token, so "no signup required to try" is actually true for the visitor
 * while the backend still has a real user + token to enforce rate limits
 * per-browser. Nothing is shown to the user during this -- it just runs
 * once in the background before they've even finished reading the page.
 */
function useGuestAuth(apiBaseUrl) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
    if (token) return; // already have one from a previous visit

    async function ensureAuth() {
      let email = localStorage.getItem("guest_email");
      let password = localStorage.getItem("guest_password");

      if (!email) {
        email = `guest-${crypto.randomUUID()}@trace.local`;
        password = crypto.randomUUID();
        localStorage.setItem("guest_email", email);
        localStorage.setItem("guest_password", password);
      }

      try {
        // First try to register -- this is the normal path for a brand
        // new guest.
        const registerRes = await fetch(`${apiBaseUrl}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password }),
        });

        if (registerRes.ok) {
          const data = await registerRes.json();
          localStorage.setItem("token", data.access_token);
          setToken(data.access_token);
          return;
        }

        // If registration failed because this guest account already
        // exists (e.g. their previous token just expired), log in with
        // the same saved credentials instead.
        const loginRes = await fetch(`${apiBaseUrl}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ username: email, password }),
        });

        if (loginRes.ok) {
          const data = await loginRes.json();
          localStorage.setItem("token", data.access_token);
          setToken(data.access_token);
        } else {
          setAuthError("Couldn't start a session. Please refresh the page.");
        }
      } catch {
        setAuthError("Couldn't reach the server. Please refresh the page.");
      }
    }

    ensureAuth();
  }, [apiBaseUrl, token]);

  return { token, authError };
}

function App() {
  const { token, authError } = useGuestAuth(API_BASE_URL);

  return (
    <div className="min-h-screen bg-ink">
      <Header />
      <Hero />

      <section id="investigate" className="mx-auto max-w-5xl px-6 py-16 sm:py-20">
        {authError && (
          <p className="mb-4 font-mono text-sm text-redAccent">{authError}</p>
        )}
        <BugForm apiBaseUrl={API_BASE_URL} authToken={token} />
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