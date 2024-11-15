import { timestamps, userMetadata } from "@db/columns.helpers";
import {
	pgTable,
	varchar,
	uuid,
	integer,
	pgEnum,
	index,
	boolean,
	unique,
	real,
	timestamp,
	primaryKey,
	numeric,
} from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm/relations";

export const users = pgTable("users", {
	id: uuid().primaryKey().defaultRandom(),
	firstName: varchar().notNull(),
	lastName: varchar().notNull(),
	email: varchar({ length: 255 }).notNull().unique(),
	...timestamps,
	...userMetadata,
});
