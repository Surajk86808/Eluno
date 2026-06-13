/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17202a",
        surface: "#f6f8fb",
        line: "#d9e0ea",
        signal: "#0f766e",
        warning: "#b45309",
        danger: "#b91c1c",
      },
    },
  },
  plugins: [],
};
