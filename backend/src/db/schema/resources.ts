import { jsonb, pgTable, varchar } from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";
import { timestamps, userMetadata } from "@db/columns.helpers";
import { policies } from "@db/schema";

export const resources = pgTable("resources", {
  id: varchar().notNull().primaryKey(),
  mappings: jsonb().notNull(),
  ...timestamps,
  ...userMetadata,
});

//MARK: - RELATIONS
export const resourceRelations = relations(resources, ({ many }) => {
  return {
    policies: many(policies),
  };
});
