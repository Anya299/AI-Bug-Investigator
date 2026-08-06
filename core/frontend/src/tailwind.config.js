/** @type {import('tailwindcss').Config} */

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}"
  ],

  theme: {
    extend: {

      colors: {

        // ---- Background system ----
        // True neutral grays, no color tint — this is what makes it read
        // "professional" instead of "gaming/dev-toy". Every background
        // step is a small, deliberate jump in lightness.
        traceBg: "#0A0A0B",
        tracePanel: "#131315",
        traceSurface: "#19191C",
        traceElevated: "#212124",

        // ---- Borders ----
        traceBorder: "rgba(255,255,255,0.09)",
        traceBorderHover: "rgba(255,255,255,0.22)",

        // ---- Text ----
        // Off-white, not pure white — pure white on near-black is what
        // makes a lot of AI-generated UIs look harsh. This is softer.
        textPrimary: "#F2F2F0",
        textSecondary: "#9B9BA1",
        textDim: "#5F5F66",

        // ---- Accent ----
        // One quiet, confident color instead of a loud neon — used only
        // on the primary CTA, the status dot, and links. Restraint is
        // what reads as expensive; covering every surface in it doesn't.
        ai: "#6C7BF0",
        aiSoft: "rgba(108,123,240,0.10)",

        warning: "#D9A24B",
        danger: "#E5646B",

        // ---- Aliases ----
        // Existing component files reference these names directly.
        // Pointed at the same values as their canonical tokens above so
        // nothing else needs to change.
        ink: "#0A0A0B",           // = traceBg
        cyan: "#6C7BF0",          // = ai
        line: "rgba(255,255,255,0.09)", // = traceBorder
        amber: "#D9A24B",         // = warning
        redAccent: "#E5646B",     // = danger

      },


      fontFamily: {

        display:[
          "Inter",
          "system-ui",
          "sans-serif"
        ],

        mono:[
          "JetBrains Mono",
          "monospace"
        ],

        // Headline now uses the same clean sans as body copy, not mono —
        // mono stays reserved for the terminal panel and small labels,
        // where the "code" association actually belongs.
        "mono-display":[
          "Inter",
          "system-ui",
          "sans-serif"
        ]

      },


      boxShadow:{

        aiGlow:
        "0 0 40px rgba(108,123,240,0.15)",

        amberGlow:
        "0 0 40px rgba(217,162,75,0.15)",

        glass:
        "0 20px 60px rgba(0,0,0,.45)",

        card:
        "0 1px 0 rgba(255,255,255,.04) inset,0 20px 50px rgba(0,0,0,.35)"

      },


      backdropBlur:{

        glass:"24px"

      },


      backgroundImage:{

        "trace-grid":
        "linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px)"

      },


      animation:{

        fadeUp:
        "fadeUp .4s ease-out",

        pulseAI:
        "pulseAI 2s infinite",

        float:
        "float 6s ease-in-out infinite",

        shimmer:
        "shimmer 2s linear infinite"

      },


      keyframes:{

        fadeUp:{
          from:{ opacity:"0", transform:"translateY(12px)" },
          to:{ opacity:"1", transform:"translateY(0)" }
        },

        pulseAI:{
          "0%,100%":{ opacity:"1", boxShadow:"0 0 0 rgba(108,123,240,0)" },
          "50%":{ opacity:".7", boxShadow:"0 0 30px rgba(108,123,240,.4)" }
        },

        float:{
          "0%,100%":{ transform:"translateY(0)" },
          "50%":{ transform:"translateY(-12px)" }
        },

        shimmer:{
          from:{ backgroundPosition:"-200% 0" },
          to:{ backgroundPosition:"200% 0" }
        }

      }

    }
  },


  plugins:[]
};