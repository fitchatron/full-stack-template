import { timestamps, userMetadata } from "@db/columns.helpers";
import { pgTable, varchar, uuid, index, unique } from "drizzle-orm/pg-core";

export const users = pgTable(
  "users",
  {
    id: uuid().primaryKey().defaultRandom(),
    firstName: varchar().notNull(),
    lastName: varchar().notNull(),
    email: varchar({ length: 255 }).notNull().unique(),
    ...timestamps,
    ...userMetadata,
  },
  (table) => [
    unique("unique_users_email").on(table.email).nullsNotDistinct(),
    index("nci_users_email").on(table.email),
  ]
);
