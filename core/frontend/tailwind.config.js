
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}"
  ],

  theme: {
    extend: {

      colors: {

        // Background system
        traceBg: "#06080d",
        tracePanel: "#0d1118",
        traceSurface: "#121823",
        traceElevated: "#18202d",

        // Borders
        traceBorder: "rgba(255,255,255,0.08)",
        traceBorderHover: "rgba(57,217,197,0.35)",


        // Text
        textPrimary: "#e6edf3",
        textSecondary: "#8b96a5",
        textDim: "#5a6472",


        // AI colors
        ai: "#39d9c5",
        aiSoft: "rgba(57,217,197,0.12)",

        warning: "#ffb454",
        danger: "#ff6b6b",

        // ---- Aliases ----
        // App.jsx / ResultPanel.jsx / TraceHero.jsx reference these names.
        // Pointed at the exact same values as their canonical counterparts
        // above so every existing class across the codebase resolves,
        // without renaming a single class in any component file.
        ink: "#06080d",           // = traceBg
        cyan: "#39d9c5",          // = ai
        line: "rgba(255,255,255,0.08)", // = traceBorder
        amber: "#ffb454",         // = warning
        redAccent: "#ff6b6b",     // = danger

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

        // Alias — App.jsx's headline uses font-mono-display.
        "mono-display":[
          "JetBrains Mono",
          "monospace"
        ]

      },


      boxShadow:{


        aiGlow:
        "0 0 40px rgba(57,217,197,0.18)",


        amberGlow:
        "0 0 40px rgba(255,180,84,0.18)",


        glass:
        "0 20px 60px rgba(0,0,0,.45)",


        card:
        "0 1px 0 rgba(255,255,255,.05) inset,0 20px 50px rgba(0,0,0,.35)"

      },


      backdropBlur:{

        glass:"24px"

      },


      backgroundImage:{


        "trace-grid":
        "linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px)"

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

          from:{
            opacity:"0",
            transform:"translateY(12px)"
          },

          to:{
            opacity:"1",
            transform:"translateY(0)"
          }

        },


        pulseAI:{


          "0%,100%":{
            opacity:"1",
            boxShadow:"0 0 0 rgba(57,217,197,0)"
          },


          "50%":{
            opacity:".7",
            boxShadow:"0 0 30px rgba(57,217,197,.5)"
          }


        },


        float:{


          "0%,100%":{
            transform:"translateY(0)"
          },


          "50%":{
            transform:"translateY(-12px)"
          }


        },


        shimmer:{


          from:{
            backgroundPosition:"-200% 0"
          },


          to:{
            backgroundPosition:"200% 0"
          }

        }


      }

    }
  },


  plugins:[]
};