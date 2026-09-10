import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        soil: {
          50: "#f4fbf4",
          100: "#dff3df",
          500: "#2f7d32",
          700: "#1b5e20",
          900: "#12361a",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
