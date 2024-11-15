import { uuid } from "drizzle-orm/pg-core";
import { timestamp } from "drizzle-orm/pg-core";

export const timestamps = {
  createdAt: timestamp().notNull().defaultNow(),
  updatedAt: timestamp().notNull().defaultNow(),
};

export const userMetadata = {
  createdBy: uuid(),
  updatedBy: uuid(),
};
