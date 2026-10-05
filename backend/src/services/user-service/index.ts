import { Request } from "express";
import { db } from "@db/db";
import { withPagination } from "@db/utils";
import { roles, userRoles, users } from "@db/schema";
import { updateUserSchema } from "@validators/user";
import { asc, eq } from "drizzle-orm";
import { eventLogger } from "@utils/logger";

export function userService() {
  const { logEvent } = eventLogger();

  async function getUsers(req: Request) {
    try {
      const page = parseInt(req.query.page?.toString() ?? "1");
      const limit = parseInt(req.query.limit?.toString() ?? "10");

      const query = db.select().from(users);

      const payload = await withPagination(
        query.$dynamic(),
        asc(users.id),
        page,
        limit,
        req,
      );

      return { data: payload, error: undefined };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to fetch users" },
      };
    }
  }

  async function getUserById(id: string) {
    try {
      const user = await db.query.users.findFirst({
        where: eq(users.id, id),
      });

      if (!user) {
        return {
          data: undefined,
          error: { code: 404, message: "Unable to get user" },
        };
      }

      return {
        data: user,
        error: undefined,
      };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to get user" },
      };
    }
  }

  async function updateUserById(id: string, body: Record<string, string>) {
    try {
      const { data: currentValue, error } = await getUserById(id);

      if (error) {
        return {
          data: undefined,
          error: error,
        };
      }

      const result = updateUserSchema.safeParse(body);
      if (!result.success) {
        throw result.error;
      }
      const newValue = result.data;
      const changes = new Set<string>();
      Object.entries(newValue).forEach(([key, value]) => {
        if (
          currentValue[
            key as keyof {
              firstName: string;
              lastName: string;
              email: string;
            }
          ] !== value
        ) {
          changes.add(key);
        }
      });

      if (changes.size === 0) {
        throw new Error("No Changes to user");
      }
      const payload: Record<string, number | string | Date | boolean> = {
        updatedAt: new Date(),
        // updatedBy: userId,
      };
      changes.forEach((changeKey) => {
        payload[changeKey] =
          newValue[
            changeKey as keyof {
              firstName: string;
              lastName: string;
              email: string;
            }
          ] ?? "";
      });
      const updated = (
        await db.update(users).set(payload).where(eq(users.id, id)).returning()
      ).at(0);

      if (!updated) throw new Error("No user returned");
      return { data: updated, error: undefined };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to update user" },
      };
    }
  }

  async function deleteUserById(id: string) {
    try {
      const rows = await db.delete(users).where(eq(users.id, id));
      return {
        data: { rows: rows.count },
        error: undefined,
      };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to delete user" },
      };
    }
  }

  async function assignRoleTo(
    userId: string,
    roleName: string,
    createdBy: string,
  ) {
    const roleToAssign = await db.query.roles.findFirst({
      where: eq(roles.name, roleName),
    });
    if (!roleToAssign) {
      logEvent({
        type: "error",
        message: `Attempted to add ${roleName} but not found`,
      });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to assign role. Role not found." },
      };
    }

    const userRole = await db
      .insert(userRoles)
      .values({
        roleId: roleToAssign.id,
        userId: userId,
        createdBy,
        updatedBy: createdBy,
      })
      .returning();

    return {
      data: userRole,
      error: undefined,
    };
  }
  return {
    getUsers,
    getUserById,
    updateUserById,
    deleteUserById,
    assignRoleTo,
  };
}
