import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        surface: {
          DEFAULT: "#0d0d0f",
          raised: "#141418",
          border: "#1f1f26",
          muted: "#2a2a35",
        },
        accent: {
          DEFAULT: "#6366f1",
          dim: "#4f46e5",
        },
      },
    },
  },
  plugins: [],
};

export default config;
