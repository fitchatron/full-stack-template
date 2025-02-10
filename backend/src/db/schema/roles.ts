import { relations } from "drizzle-orm";
import { index, pgTable, unique, uuid, varchar } from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";
import { userRoles } from "@db/schema/user-roles";
import { rolePermissions } from "@db/schema/role-permissions";
import { rolePolicies } from "@db/schema/role-policies";

export const roles = pgTable(
  "roles",
  {
    id: uuid().notNull().primaryKey().defaultRandom(),
    name: varchar().notNull(),
    description: varchar().notNull(),
    ...timestamps,
    ...userMetadata,
  },
  (table) => [
    unique("unique_roles_name").on(table.name).nullsNotDistinct(),
    index("nci_roles_name").on(table.name),
  ],
);

//MARK: - RELATIONS
export const rolesRelations = relations(roles, ({ many }) => {
  return {
    userRoles: many(userRoles),
    rolePermissions: many(rolePermissions),
    rolePolicies: many(rolePolicies),
  };
});
