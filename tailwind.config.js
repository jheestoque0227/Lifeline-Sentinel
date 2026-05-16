const flowbite = require("flowbite/plugin");

module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js",
    "./node_modules/flowbite/**/*.js"
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      colors: {
        primary: "#2756A5",
        secondary: "#5A90AD",
        accent: "#70B5D9",
        cyanSoft: "#8ACCE5",
        appBg: "#EAF2F6",
        sentinel: {
          50: "#EAF2F6",
          100: "#D8ECF4",
          200: "#8ACCE5",
          300: "#70B5D9",
          500: "#5A90AD",
          600: "#2756A5",
          700: "#1F4584",
          900: "#162D56"
        }
      },
      boxShadow: {
        soft: "0 18px 45px rgba(39, 86, 165, 0.10)"
      }
    }
  },
  plugins: [flowbite]
};
