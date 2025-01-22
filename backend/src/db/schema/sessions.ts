import { relations } from "drizzle-orm";
import { pgTable, timestamp, uuid, varchar } from "drizzle-orm/pg-core";
import { users } from "@db/schema/users";

export const sessions = pgTable("sessions", {
  id: uuid().notNull().primaryKey().defaultRandom(),
  token: varchar().notNull().unique(),
  userId: uuid()
    .notNull()
    .references(() => users.id),
  ipAddress: varchar(),
  userAgent: varchar(),
  createdAt: timestamp().notNull().defaultNow(),
  expiresAt: timestamp().notNull().defaultNow(),
});

//MARK: - RELATIONS
export const sessionsRelations = relations(sessions, ({ one }) => {
  return {
    user: one(users, {
      fields: [sessions.userId],
      references: [users.id],
    }),
  };
});
