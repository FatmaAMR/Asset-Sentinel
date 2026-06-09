/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Crisp, premium light gray background
        dark: "#F8FAFC",           
        "cards-dark": "#FFFFFF",   
        "cards-light": "#FFFFFF",  
        
        // Brand Identity (Taken from your logo)
        primary: "#1E3A8A",        // Rich Navy Blue
        accent: "#3B82F6",         // Bright Electric Blue for pops
        
        // Refined status pops (not overwhelming)
        normal: "#059669",         // Emerald Green
        warning: "#D97706",        // Amber
        failure: "#DC2626",        // Clean Crimson Red
        
        // Typography & UI Elements
        light: "#0F172A",          // Deep charcoal-navy for text
        muted: "#475569",          // Slate gray for secondary details
        borderSubtle: "#F1F5F9",   // Softest gray for dividers
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
};
