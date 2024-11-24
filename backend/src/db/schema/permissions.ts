import { pgTable, uuid, varchar } from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";
import { rolePermissions } from "@db/schema/role-permissions";
import { relations } from "drizzle-orm";

export const permissions = pgTable("permissions", {
  id: uuid().notNull().primaryKey().defaultRandom(),
  name: varchar().notNull(),
  description: varchar().notNull(),
  ...timestamps,
  ...userMetadata,
});

//MARK: - RELATIONS
export const permissionsRelations = relations(permissions, ({ many }) => {
  return {
    rolePermissions: many(rolePermissions),
  };
});
