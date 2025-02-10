import { jsonb, pgTable, uuid, varchar } from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";
import {
  rolePolicies,
  resources,
  policyActionEnum,
  policyDecisionEnum,
} from "@db/schema";
import { relations } from "drizzle-orm";

export const policies = pgTable("policies", {
  id: uuid().notNull().primaryKey().defaultRandom(),
  resource: varchar()
    .notNull()
    .references(() => resources.id),
  action: policyActionEnum().notNull(),
  condition: jsonb(),
  decision: policyDecisionEnum().notNull().default("allow"),
  ...timestamps,
  ...userMetadata,
});

//MARK: - RELATIONS
export const policiesRelations = relations(policies, ({ many, one }) => {
  return {
    rolePolicies: many(rolePolicies),
    resource: one(resources),
  };
});
