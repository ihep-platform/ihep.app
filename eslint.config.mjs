import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // Allow underscore-prefixed unused vars (intentional: callback params, rest patterns)
    rules: {
      "@typescript-eslint/no-unused-vars": ["error", {
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
