import dotenv from "dotenv";
dotenv.config();

import { defineConfig } from "drizzle-kit";
export default defineConfig({
  dialect: "postgresql",
  schema: "./src/db/schema",
  out: "./src/db/migrations",
  dbCredentials: {
    url: process.env.DATABASE_URL ?? "",
  },
  verbose: true,
  strict: true,
  casing: "snake_case",
  migrations: {
    table: "__drizzle_migrations",
    schema: "drizzle",
  },
});
