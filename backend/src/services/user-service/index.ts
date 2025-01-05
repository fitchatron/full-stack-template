import { Request } from "express";
import { db } from "@db/db";
import { withPagination } from "@db/utils";
import { users } from "@db/schema";
import { addUserSchema, updateUserSchema } from "@validators/user";
import { asc, eq } from "drizzle-orm";
import { eventLogger } from "@utils/logger";

export function userService() {
  async function getUsers(req: Request) {
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

    return payload;
  }

  async function createUser(req: Request): Promise<{
    data?: {
      id: string;
      firstName: string;
      lastName: string;
      email: string;
      createdBy: string | null;
      createdAt: Date;
      updatedBy: string | null;
      updatedAt: Date;
    };
    error?: { code: number; message: string };
  }> {
    try {
      const result = addUserSchema.safeParse(req.body);
      if (!result.success) {
        throw result.error;
      }
      const user = (await db.insert(users).values(result.data).returning()).at(
        0,
      );
      if (!user) throw new Error("No user returned");
      return { data: user, error: undefined };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create user" },
      };
    }
  }

  async function getUserById(id: string) {
    return db.query.users.findFirst({
      where: eq(users.id, id),
    });
  }

  async function updateUserById(id: string, body: Record<string, string>) {
    try {
      const currentValue = await getUserById(id);
      if (!currentValue) {
        return {
          data: undefined,
          error: { code: 404, message: "Unable to get user" },
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
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to update user" },
      };
    }
  }

  async function deleteUserById(id: string) {
    const rows = await db.delete(users).where(eq(users.id, id));
    return rows.count;
  }

  return { getUsers, createUser, getUserById, updateUserById, deleteUserById };
}
