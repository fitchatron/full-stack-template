import { jsonb, pgTable, uuid, varchar } from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";
import { rolePolicies } from "@db/schema/role-policies";
import { relations } from "drizzle-orm";
import { policyActionEnum, policyDecisionEnum } from "@db/schema/enums";

export const policies = pgTable("policies", {
  id: uuid().notNull().primaryKey().defaultRandom(),
  resource: varchar().notNull(),
  action: policyActionEnum().notNull(),
  condition: jsonb(),
  decision: policyDecisionEnum().notNull().default("allow"),
  ...timestamps,
  ...userMetadata,
});

//MARK: - RELATIONS
export const policiesRelations = relations(policies, ({ many }) => {
  return {
    rolePolicies: many(rolePolicies),
  };
});
