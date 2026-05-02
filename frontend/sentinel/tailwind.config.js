/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#7C3AED",
        light: "#F9FAFB",
        dark: "#111827",
        "cards-light": "#FFFFFF",
        "cards-dark": "#1F2937",
        warning: "#FDE047",
        failure: "#EF4444",
        normal: "#10B981",
        accent: "#FACC15",
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
