import {
  pgTable,
  primaryKey,
  serial,
  uuid,
  varchar,
} from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";
import { roles } from "@db/schema/roles";
import { users } from "@db/schema/users";
import { relations } from "drizzle-orm";

export const userRoles = pgTable(
  "user_roles",
  {
    userId: uuid()
      .notNull()
      .references(() => users.id),
    roleId: uuid()
      .notNull()
      .references(() => roles.id),
    ...timestamps,
    ...userMetadata,
  },
  (table) => [
    primaryKey({
      name: "pk_user_roles_user_id_role_id",
      columns: [table.userId, table.roleId],
    }),
  ],
);

// MARK: -  RELATIONS
export const userRolesRelations = relations(userRoles, ({ one }) => ({
  role: one(roles, {
    fields: [userRoles.roleId],
    references: [roles.id],
  }),
  user: one(users, {
    fields: [userRoles.userId],
    references: [users.id],
  }),
}));
