import globals from "globals";
import pluginJs from "@eslint/js";
import tseslint from "typescript-eslint";

/** @type {import('eslint').Linter.Config[]} */
export default [
  {
    files: ["**/*.{js,mjs,cjs,ts,jsx,tsx,cts}"],
    ignores: ["**/.*", "**/dist ", "**/node_modules"],
  },
  {
    languageOptions: { globals: globals.node }, rules: {
      "no-unused-vars": ["error", {
        "vars": "all",
        "args": "after-used",
        "caughtErrors": "all",
        "ignoreRestSiblings": false,
        "reportUsedIgnorePattern": false
      }]
    }
  },
  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
];
