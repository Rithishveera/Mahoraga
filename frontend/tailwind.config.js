module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        "m-void":    "#121212",
        "m-void2":   "#1a1a1a",
        "m-surface": "#1e1e1e",
        "m-surface2":"#242424",
        "m-crimson": "#FF3B30",
        "m-amber":   "#FF9F0A",
        "m-silver":  "#E5E5EA",
        "m-dim":     "#3a3a3a",
        "m-muted":   "#6e6e73",
        "m-faint":   "#2a2a2a",
      },
      fontFamily: {
        mono:    ["JetBrains Mono", "Fira Code", "monospace"],
        display: ["Syne", "sans-serif"],
        body:    ["DM Sans", "sans-serif"],
      },
      animation: {
        "pulse-crimson": "pulseCrimson 2s ease-in-out infinite",
        "pulse-amber":   "pulseAmber 2.5s ease-in-out infinite",
        "slide-up":      "slideUp 0.4s cubic-bezier(0.16,1,0.3,1)",
        "slide-in":      "slideInTop 0.3s ease-out",
        "scan":          "scan 4s linear infinite",
        "flicker":       "flicker 5s ease-in-out infinite",
        "fade-in":       "fadeIn 0.3s ease-out",
        "breathe":       "breathe 3s ease-in-out infinite",
      },
      keyframes: {
        pulseCrimson: {
          "0%,100%": { opacity: "0.5", filter: "drop-shadow(0 0 4px #FF3B30)" },
          "50%":     { opacity: "1",   filter: "drop-shadow(0 0 12px #FF3B30)" },
        },
        pulseAmber: {
          "0%,100%": { opacity: "0.5", filter: "drop-shadow(0 0 4px #FF9F0A)" },
          "50%":     { opacity: "1",   filter: "drop-shadow(0 0 12px #FF9F0A)" },
        },
        slideUp: {
          "0%":   { transform: "translateY(16px)", opacity: "0" },
          "100%": { transform: "translateY(0)",    opacity: "1" },
        },
        slideInTop: {
          "from": { transform: "translateY(-10px)", opacity: "0" },
          "to":   { transform: "translateY(0)",     opacity: "1" },
        },
        scan: {
          "0%":   { top: "-2px" },
          "100%": { top: "110%" },
        },
        flicker: {
          "0%,89%,91%,95%,100%": { opacity: "1" },
          "90%": { opacity: "0.3" },
          "93%": { opacity: "0.7" },
          "94%": { opacity: "0.3" },
        },
        fadeIn: {
          "from": { opacity: "0" },
          "to":   { opacity: "1" },
        },
        breathe: {
          "0%,100%": { transform: "scale(1)",    opacity: "0.6" },
          "50%":     { transform: "scale(1.05)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
}
