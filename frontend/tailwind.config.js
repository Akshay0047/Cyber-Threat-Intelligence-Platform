/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Rajdhani", "Segoe UI", "sans-serif"],
        display: ["Orbitron", "Rajdhani", "sans-serif"],
      },
      boxShadow: {
        inset: "inset 0 1px 0 rgba(255,255,255,0.04), inset 0 8px 18px rgba(0,0,0,0.35)",
        glow: "0 0 22px rgba(34, 211, 238, 0.35)",
      },
    },
  },
  plugins: [],
};
