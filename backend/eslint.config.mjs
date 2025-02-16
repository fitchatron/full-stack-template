// @ts-check

import js from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import prettierConfig from "eslint-config-prettier";
import jest from "eslint-plugin-jest"


export default [
    {
        files: ["**/*.ts", "**/*.tsx"],
        languageOptions: {
            parser: tsparser,
            sourceType: "module",
        },
        plugins: {
            "@typescript-eslint": tseslint,
            jest: jest,
        },
        rules: {
            "@typescript-eslint/consistent-type-definitions": ["warn", "type"],
            "jest/no-disabled-tests": "warn",
        },
    },
    js.configs.recommended,
    tseslint.configs.recommended,
    tseslint.configs.strict,
    tseslint.configs.stylistic,
    prettierConfig,
    {
        extends: ["plugin:jest/recommended"],
    },
];