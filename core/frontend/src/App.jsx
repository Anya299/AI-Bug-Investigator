import CursorGlow from "./components/CursorGlow";
import { useEffect, useRef, useState } from "react";
import TraceHero from "./components/TraceHero";
import BugForm from "./components/BugForm";
import Reveal from "./components/Reveal";
import IntroScreen from "./components/IntroScreen";
import HowItWorks from "./components/HowItWorks";
import SectionNav from "./components/SectionNav";

import GlassCard from "./components/ui/GlassCard";
import AIStatus from "./components/ui/AIStatus";
import GlowOrb from "./components/ui/GlowOrb";
import PrimaryButton from "./components/ui/PrimaryButton";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const SECTIONS = [
  { id: "hero", label: "Home" },
  { id: "how", label: "How it works" },
  { id: "investigate", label: "Workspace" },
];

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
  const [introDone, setIntroDone] = useState(false);

  const scrollContainerRef = useRef(null);
  const heroRef = useRef(null);
  const howRef = useRef(null);
  const workspaceRef = useRef(null);
  const sectionRefs = { hero: heroRef, how: howRef, investigate: workspaceRef };

  // Once the intro finishes, jump straight to the workspace slide —
  // no click, no scroll needed from the visitor.
  useEffect(() => {
    if (!introDone) return;
    workspaceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [introDone]);

  return (
  <div
    className="
    relative
    h-screen
    overflow-hidden
    bg-traceBg
    text-textPrimary
    "
  >

    {!introDone && <IntroScreen onComplete={() => setIntroDone(true)} />}

    {/* Ambient background — fixed so it stays put as slides change,
        instead of scrolling away with the content. */}
    <CursorGlow />
    <div className="pointer-events-none fixed inset-0 trace-grid opacity-40" />
    <GlowOrb className="fixed -top-40 left-1/3 h-96 w-96" />
    <GlowOrb className="fixed right-0 top-1/2 h-72 w-72" />

    <Header />
    <SectionNav sections={SECTIONS} refs={sectionRefs} containerRef={scrollContainerRef} />

    {/* Scroll-snap slide container — one full-viewport section at a time,
        the way Apple/Framer-style product pages move between slides,
        instead of one continuous long scroll. */}
    <main
      ref={scrollContainerRef}
      className="relative z-10 h-screen snap-y snap-mandatory overflow-y-auto scroll-smooth"
    >

      <Hero innerRef={heroRef} />

      <HowItWorks innerRef={howRef} />

      <section
        ref={workspaceRef}
        id="investigate"
        className="
        flex
        min-h-screen
        snap-start
        snap-always
        flex-col
        justify-center
        pt-24
        "
      >

        <div className="mx-auto w-full max-w-6xl px-6 py-10">

          <Reveal>
            <div className="mb-8 flex items-center justify-between">

              <div>
                <h2 className="text-3xl font-bold">
                  Investigation Workspace
                </h2>

                <p className="mt-2 text-textSecondary">
                  Paste evidence. Let Trace find the root cause.
                </p>

              </div>


              <AIStatus />

            </div>
          </Reveal>



          {authError && (
            <p className="mb-4 font-mono text-sm text-redAccent">
              {authError}
            </p>
          )}



          <Reveal delay={150}>
            <GlassCard
              className="
              trace-hover-lift
              p-6
              sm:p-10
              "
            >

              <BugForm
                apiBaseUrl={API_BASE_URL}
                authToken={token}
              />

            </GlassCard>
          </Reveal>

        </div>

        <Footer />

      </section>

    </main>

  </div>
);
}

function Header() {
  return (
    <header className="trace-nav fixed inset-x-0 top-0 z-50">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">

        <div className="flex items-center gap-3">
          <div className="relative">
            <span className="block h-3 w-3 rounded-full bg-cyan" />
            <span className="absolute inset-0 h-3 w-3 animate-ping rounded-full bg-cyan opacity-50" />
          </div>

          <span className="font-display text-lg font-bold tracking-tight text-textPrimary">
            trace
          </span>
        </div>


        <nav className="flex items-center gap-4">

          <a
            href="#investigate"
            className="
            hidden
            text-xs
            font-mono
            text-textSecondary
            transition-colors
            hover:text-cyan
            sm:block
            "
          >
            Live demo
          </a>


          <a
            href="#investigate"
            className="
            rounded-lg
            border
            border-cyan/40
            bg-cyan/10
            px-4
            py-2
            text-xs
            font-mono
            text-cyan
            transition
            hover:bg-cyan/20
            "
          >
            Investigate →
          </a>

        </nav>

      </div>
    </header>
  );
}

function Hero({ innerRef }) {
  return (
    <section
      ref={innerRef}
      id="hero"
      className="flex h-screen snap-start snap-always items-center"
    >
      <div className="mx-auto grid w-full max-w-6xl gap-12 px-6 pt-20 lg:grid-cols-2 lg:items-center">

        <Reveal direction="left">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.25em] text-textDim">
            AI debugging infrastructure
           </p>

            <h1 className="mt-6 font-display text-5xl font-bold leading-[1.05] tracking-tight text-textPrimary sm:text-6xl lg:text-7xl">

              Debugging,
              <br />

              investigated.

             </h1>

            <p className="mt-6 max-w-xl text-lg leading-relaxed text-textSecondary">

            Paste an error. Get the root cause and the fix — not a guess.

           </p>
            <div className="mt-10 flex flex-wrap items-center gap-4">

            <a href="#investigate">
              <PrimaryButton>
                Start investigating →
             </PrimaryButton>
           </a>


            <button
            className="
            rounded-xl
            border
            border-line
            px-6
            py-3
            font-mono
            text-sm
            text-textSecondary
            transition
            hover:border-cyan
            hover:text-cyan
            "
           >
           View dashboard
           </button>


           </div>
          </div>
        </Reveal>

        <Reveal direction="right" delay={150}>
          <TraceHero />
        </Reveal>

      </div>
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