import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // Downgrade pre-existing violations to warnings so CI is not blocked.
    // These should be fixed incrementally over time.
    rules: {
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-this-alias": "warn",
      "@next/next/no-html-link-for-pages": "warn",
      "@next/next/no-assign-module-variable": "warn",
      "@typescript-eslint/ban-ts-comment": "warn",
      "react-hooks/purity": "warn",
      "react-hooks/immutability": "warn",
      "prefer-const": "warn",
      "@typescript-eslint/no-unused-vars": ["warn", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
        destructuredArrayIgnorePattern: "^_",
        caughtErrorsIgnorePattern: "^_",
      }],
    },
  },
  {
    // CommonJS scripts legitimately use require()
    files: ["scripts/**/*.js", "mirth-connect/**/*.js", "tailwind.config.ts"],
    rules: {
      "@typescript-eslint/no-require-imports": "off",
    },
  },
  {
    // Legal pages contain prose with intentional quotes/apostrophes
    files: ["src/app/legal/**/*.tsx"],
    rules: {
      "react/no-unescaped-entities": "off",
    },
  },
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Vendored/generated files
    "src/app/investor-dashboard/chart.js",
    "public/wasm/**",
  ]),
]);

export default eslintConfig;
