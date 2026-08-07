import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import LandingExperience from "./components/LandingExperience";
import InvestigationWorkspace from "./components/InvestigationWorkspace";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

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

  // The single source of truth for which experience is showing. Nothing
  // scroll-based decides this anymore — that was the root cause of
  // landing on the workspace and having to scroll up to find the hero.
  const [view, setView] = useState("landing"); // "landing" | "workspace"

  return (
    <div className="relative min-h-screen bg-traceBg text-textPrimary">
      <AnimatePresence mode="wait">

        {view === "landing" ? (
          <motion.div
            key="landing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, scale: 1.04, filter: "blur(16px)" }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <LandingExperience onStartInvestigation={() => setView("workspace")} />
          </motion.div>
        ) : (
          <motion.div
            key="workspace"
            initial={{ opacity: 0, scale: 0.97, filter: "blur(16px)" }}
            animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <InvestigationWorkspace
              apiBaseUrl={API_BASE_URL}
              authToken={token}
              authError={authError}
              onBackToHome={() => setView("landing")}
            />
          </motion.div>
        )}

      </AnimatePresence>
    </div>
  );
}

export default App;