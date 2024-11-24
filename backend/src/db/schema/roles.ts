import { relations } from "drizzle-orm";
import { pgTable, uuid, varchar } from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";
import { userRoles } from "@db/schema/user-roles";
import { rolePermissions } from "@db/schema/role-permissions";

export const roles = pgTable("roles", {
  id: uuid().notNull().primaryKey().defaultRandom(),
  name: varchar().notNull(),
  description: varchar().notNull(),
  ...timestamps,
  ...userMetadata,
});

//MARK: - RELATIONS
export const rolesRelations = relations(roles, ({ many }) => {
  return {
    userRoles: many(userRoles),
    rolePermissions: many(rolePermissions),
  };
});
