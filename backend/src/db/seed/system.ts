import { db } from "@db/db";
import {
  policies,
  resources,
  rolePolicies,
  roles,
  sessions,
  userRoles,
  users,
} from "@db/schema";
import { NewUser } from "@models/orm-model";

export async function createSystemUser() {
  const admin: NewUser = {
    firstName: "SYSTEM",
    lastName: "SYSTEM",
    email: "SYSTEM@email.com",
    passwordHash: "hash",
    salt: "salt",
  };

  await db.insert(users).values(admin);
}

export async function truncateTables() {
  await db.delete(sessions);
  await db.delete(userRoles);
  await db.delete(rolePolicies);
  await db.delete(resources);
  await db.delete(roles);
  await db.delete(policies);
  await db.delete(users);
}
