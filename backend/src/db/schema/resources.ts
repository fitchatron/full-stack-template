import { jsonb, pgTable, varchar } from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";

export const resources = pgTable("resources", {
  id: varchar().notNull().primaryKey(),
  mappings: jsonb().notNull(),
  ...timestamps,
  ...userMetadata,
});
