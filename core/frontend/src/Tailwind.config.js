/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0e14",
        surface: "#12161f",
        surfaceRaised: "#171c27",
        line: "#232a38",
        textPrimary: "#e6edf3",
        textSecondary: "#8b96a5",
        textDim: "#5a6472",
        amber: "#ffb454",
        cyan: "#39d9c5",
        redAccent: "#ff6b6b",
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glowCyan: "0 0 0 1px rgba(57,217,197,0.15), 0 8px 30px -8px rgba(57,217,197,0.25)",
        glowAmber: "0 0 0 1px rgba(255,180,84,0.15), 0 8px 30px -8px rgba(255,180,84,0.25)",
        card: "0 1px 0 rgba(255,255,255,0.03) inset, 0 20px 40px -24px rgba(0,0,0,0.6)",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        ringFill: {
          "0%": { strokeDashoffset: "251" },
        },
      },
      animation: {
        shimmer: "shimmer 1.8s linear infinite",
        fadeUp: "fadeUp 0.35s ease-out",
      },
    },
  },
  plugins: [],
};