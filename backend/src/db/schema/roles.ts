import { timestamps, userMetadata } from "@db/columns.helpers";
import { pgTable, primaryKey, serial, varchar } from "drizzle-orm/pg-core";

export const roles = pgTable("roles", {
  id: serial().notNull().primaryKey(),
  name: varchar().notNull(),
  description: varchar().notNull(),
  ...timestamps,
  ...userMetadata,
});

export const permissions = pgTable("permissions", {
  id: serial().notNull().primaryKey(),
  name: varchar().notNull(),
  description: varchar().notNull(),
  ...timestamps,
  ...userMetadata,
});

export const userRoles = pgTable(
  "user_roles",
  {
    userId: varchar().notNull(),
    roleId: serial().notNull(),
    ...timestamps,
    ...userMetadata,
  },
  (table) => [
    primaryKey({
      name: "pk_user_roles_user_id_role_id",
      columns: [table.userId, table.roleId],
    }),
  ]
);

export const rolePermissions = pgTable(
  "role_permissions",
  {
    roleId: serial().notNull(),
    permissionId: serial().notNull(),
    ...timestamps,
    ...userMetadata,
  },
  (table) => [
    primaryKey({
      name: "pk_role_permissions_role_id_permission_id",
      columns: [table.roleId, table.permissionId],
    }),
  ]
);
