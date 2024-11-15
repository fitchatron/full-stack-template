import dotenv from "dotenv";
dotenv.config();

import { drizzle } from "drizzle-orm/postgres-js";
import * as schema from "@db/schema/index";
import postgres from "postgres";

const client = postgres(process.env.DATABASE_URL ?? "");
export const db = drizzle(client, {
  schema,
  logger: true,
  casing: "snake_case",
});
