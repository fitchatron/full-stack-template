/**
 * For a detailed explanation regarding each configuration property, visit:
 * https://jestjs.io/docs/configuration
 */

import type { Config } from "jest";

const config: Config = {
  clearMocks: true,
  collectCoverage: true,
  preset: "ts-jest",
  testEnvironment: "node",
  testPathIgnorePatterns: ["/node_modules/"],
  extensionsToTreatAsEsm: [".ts", ".tsx"],
  setupFilesAfterEnv: ["<rootDir>/__test__/jest.setup.ts"],
  // rootDir: "./",
  moduleNameMapper: {
    "^@api\/(.*)$": "<rootDir>/src/api/$1",
    "^@db\/(.*)$": "<rootDir>/src/db/$1",
    "^@docs\/(.*)$": "<rootDir>/src/docs/$1",
    "^@middleware\/(.*)$": "<rootDir>/src/middleware/$1",
    "^@models\/(.*)$": "<rootDir>/src/models/$1",
    "^@services\/(.*)$": "<rootDir>/src/services/$1",
    "^@test\/(.*)$": "<rootDir>/__test__/$1",
    "^@utils\/(.*)$": "<rootDir>/src/utils/$1",
    "^@validators\/(.*)$": "<rootDir>/src/validators/$1",
  },
  resolver: undefined,
};

// console.log("Jest rootDir:", __dirname);

export default config;
