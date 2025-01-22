import { relations } from "drizzle-orm";
import { pgTable, varchar, uuid, index, unique } from "drizzle-orm/pg-core";
import { timestamps, userMetadata } from "@db/columns.helpers";
import { userRoles } from "@db/schema/user-roles";
import { sessions } from "@db/schema/sessions";

export const users = pgTable(
  "users",
  {
    id: uuid().primaryKey().defaultRandom(),
    firstName: varchar().notNull(),
    lastName: varchar().notNull(),
    passwordHash: varchar().notNull(),
    salt: varchar().notNull(),
    email: varchar({ length: 255 }).notNull().unique(),
    ...timestamps,
    ...userMetadata,
  },
  (table) => [
    unique("unique_users_email").on(table.email).nullsNotDistinct(),
    index("nci_users_email").on(table.email),
  ],
);

//MARK: - RELATIONS
export const usersRelations = relations(users, ({ many }) => {
  return {
    userRoles: many(userRoles),
    sessions: many(sessions),
  };
});
