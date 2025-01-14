import { Request } from "express";
import { cryptoService } from "@utils/crypto";
import { db } from "@db/db";
import { withPagination } from "@db/utils";
import { users } from "@db/schema";
import { addUserSchema, updateUserSchema } from "@validators/user";
import { asc, eq } from "drizzle-orm";
import { eventLogger } from "@utils/logger";

export function userService() {
  const { generateSaltAndHash } = cryptoService();

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
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to fetch users" },
      };
    }
  }

  async function createUser(req: Request) {
    try {
      const result = addUserSchema.safeParse({
        ...req.body,
        // createdBy: "b2d12509-ecc1-4bb3-ae22-550afe76af95",
        // modifiedBy: "b2d12509-ecc1-4bb3-ae22-550afe76af95",
      });
      if (!result.success) {
        const fieldErrors = result.error.flatten().fieldErrors;
        const validationErrors = Object.entries(fieldErrors).map(
          ([field, errors]) => {
            return `${field}: ${errors.join("\n")}`;
          },
        );
        return {
          data: undefined,
          error: {
            code: 400,
            message: `Failed to Create user. Missing or invalid data. ${validationErrors}`,
          },
        };
      }

      // Hash password
      const { salt, hash } = await generateSaltAndHash(result.data.password);

      const user = (
        await db
          .insert(users)
          .values({
            firstName: result.data.firstName,
            lastName: result.data.lastName,
            email: result.data.email,
            passwordHash: hash,
            salt: salt,
          })
          .returning()
      ).at(0);
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
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
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
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
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
        data: rows.count,
        error: undefined,
      };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to delete user" },
      };
    }
  }

  return { getUsers, createUser, getUserById, updateUserById, deleteUserById };
}
