import { faker } from "@faker-js/faker";
import { db } from "@db/db";
import { seedPolicies } from "@db/seed/policies";
import { createSystemUser, truncateTables } from "@db/seed/system";
import { cryptoService } from "@utils/crypto";
import { roles, sessions, userRoles, users } from "@db/schema";
import { NewSession, NewUser, NewUserRole } from "@models/orm-model";
import { randomBytes } from "crypto";
import { eq } from "drizzle-orm";
import { seedResources } from "./resources";

faker.seed(4);
const { generateSaltAndHash } = cryptoService();

async function seedUsers() {
  const {
    sessions: newSessions,
    users: newUsers,
    userRoles: newUserRoles,
  } = await createUsers({
    admin: { count: 1 },
    public: {
      count: 50,
      sessions: 5,
    },
    "user-admin": {
      count: 10,
      sessions: 5,
    },
  });

  const userRows = await db.insert(users).values(newUsers).returning();
  console.log(`👤 ${userRows.length} users seeded...\n`);

  const userRoleRows = await db
    .insert(userRoles)
    .values(newUserRoles)
    .returning();
  console.log(`👩‍💼 ${userRoleRows.length} user roles seeded...\n`);

  const sessionRows = await db.insert(sessions).values(newSessions).returning();
  console.log(`🍪 ${sessionRows.length} sessions seeded...\n`);
}

async function createUser(
  roleName?: "admin" | "public" | "user-admin",
  session?: boolean,
) {
  const password = faker.internet.password();
  const { salt, hash } = await generateSaltAndHash(password);
  const user: NewUser = {
    id: faker.string.uuid(),
    firstName: faker.person.firstName(),
    lastName: faker.person.lastName(),
    email: faker.internet.email(),
    passwordHash: hash,
    salt,
  };

  let newSession: NewSession | undefined;
  let newUserRole: NewUserRole | undefined;

  if (session ?? false) {
    newSession = {
      userId: user.id ?? "",
      token: randomBytes(32).toString("hex"),
    };
  }

  if (roleName) {
    const role = await db.query.roles.findFirst({
      where: eq(roles.name, roleName),
    });
    if (role) {
      newUserRole = {
        userId: user.id ?? "",
        roleId: role.id,
      };
    }
  }

  return { user, session: newSession, userRole: newUserRole };
}

async function createUsers(
  options: Record<
    "admin" | "public" | "user-admin",
    { count: number; sessions?: number }
  >,
) {
  const users: NewUser[] = [];
  const sessions: NewSession[] = [];
  const userRoles: NewUserRole[] = [];
  for (const [key, value] of Object.entries(options)) {
    let sessionsCreated = 0;
    for (let index = 0; index < value.count; index++) {
      const { user, session, userRole } = await createUser(
        key as "admin" | "public" | "user-admin",
        sessionsCreated <= (value.sessions ?? 0),
      );
      users.push(user);
      if (session) {
        sessions.push(session);
        sessionsCreated++;
      }

      if (userRole) {
        userRoles.push(userRole);
      }
    }
  }

  return { users, sessions, userRoles };
}

const main = async () => {
  try {
    console.log("🏁 Start seeding the database...\n");

    await truncateTables();
    console.log("🧨 Database truncated...\n");

    await createSystemUser();
    console.log("🦸 Admin user created...\n");

    await seedResources();
    console.log(`📋 resources created...\n`);

    await seedPolicies();
    console.log("🕵️‍♀️ Roles and policies created...\n");

    await seedUsers();
    console.log("💁‍♀️ Users created...\n");
    console.log("\n🏁 Finished seeding the database successfully...\n");
  } catch (error) {
    console.error("❌ Seeding failed:", error);
    process.exit(1); // Exit with error code 1
  } finally {
    process.exit(0); // Exit gracefully when everything is done
  }
};

main();
