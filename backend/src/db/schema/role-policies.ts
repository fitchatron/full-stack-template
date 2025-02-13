import { pgTable, primaryKey, uuid } from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";
import { relations } from "drizzle-orm";
import { roles } from "@db/schema/roles";
import { policies } from "@db/schema/policies";

export const rolePolicies = pgTable(
  "role_policies",
  {
    roleId: uuid()
      .notNull()
      .references(() => roles.id),
    policyId: uuid()
      .notNull()
      .references(() => policies.id),
    ...timestamps,
    ...userMetadata,
  },
  (table) => [
    primaryKey({
      name: "pk_role_policies_role_id_policy_id",
      columns: [table.roleId, table.policyId],
    }),
  ],
);

// MARK: -  RELATIONS
export const rolePoliciesRelations = relations(rolePolicies, ({ one }) => ({
  role: one(roles, {
    fields: [rolePolicies.roleId],
    references: [roles.id],
  }),
  policy: one(policies, {
    fields: [rolePolicies.policyId],
    references: [policies.id],
  }),
}));
