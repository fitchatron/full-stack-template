import { pgTable, primaryKey, uuid } from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";
import { relations } from "drizzle-orm";
import { roles } from "@db/schema/roles";
import { permissions } from "@db/schema/permissions";

export const rolePermissions = pgTable(
  "role_permissions",
  {
    roleId: uuid()
      .notNull()
      .references(() => roles.id),
    permissionId: uuid()
      .notNull()
      .references(() => permissions.id),
    ...timestamps,
    ...userMetadata,
  },
  (table) => [
    primaryKey({
      name: "pk_role_permissions_role_id_permission_id",
      columns: [table.roleId, table.permissionId],
    }),
  ],
);

// MARK: -  RELATIONS
export const rolePermissionsRelations = relations(
  rolePermissions,
  ({ one }) => ({
    role: one(roles, {
      fields: [rolePermissions.roleId],
      references: [roles.id],
    }),
    permission: one(permissions, {
      fields: [rolePermissions.permissionId],
      references: [permissions.id],
    }),
  }),
);
