import { Request } from "express";
import { db } from "@db/db";
import { withPagination } from "@db/utils";
import { roles } from "@db/schema";
import { asc, eq } from "drizzle-orm";
import { eventLogger } from "@utils/logger";
import { parseZodErrorToResponse } from "@utils/error";
import { addRoleSchema, updateRoleSchema } from "@validators/role";

export function roleService() {
  const { logEvent } = eventLogger();

  async function getRoles(req: Request) {
    try {
      const page = parseInt(req.query.page?.toString() ?? "1");
      const limit = parseInt(req.query.limit?.toString() ?? "10");

      const query = db.select().from(roles);

      const payload = await withPagination(
        query.$dynamic(),
        asc(roles.id),
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

  async function createRole(req: Request) {
    try {
      const result = addRoleSchema.safeParse(req.body);
      if (!result.success) {
        return parseZodErrorToResponse(result.error);
      }
      const role = await db.insert(roles).values(result.data).returning();

      return { data: role, error: undefined };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create role" },
      };
    }
  }

  async function getRoleById(id: string) {
    try {
      const role = await db.query.roles.findFirst({
        where: eq(roles.id, id),
      });

      if (!role) {
        return {
          data: undefined,
          error: { code: 404, message: "Unable to get role" },
        };
      }

      return {
        data: role,
        error: undefined,
      };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to get role" },
      };
    }
  }

  async function updateRoleById(id: string, body: Record<string, string>) {
    try {
      const { data: currentValue, error } = await getRoleById(id);

      if (error) {
        return {
          data: undefined,
          error: error,
        };
      }

      const result = updateRoleSchema.safeParse(body);
      if (!result.success) {
        throw result.error;
      }
      const newValue = result.data;
      const changes = new Set<string>();
      Object.entries(newValue).forEach(([key, value]) => {
        if (
          currentValue[
            key as keyof {
              name: string;
              description: string;
            }
          ] !== value
        ) {
          changes.add(key);
        }
      });

      if (changes.size === 0) {
        throw new Error("No Changes to role");
      }
      const payload: Record<string, number | string | Date | boolean> = {
        updatedAt: new Date(),
        // updatedBy: userId,
      };
      changes.forEach((changeKey) => {
        payload[changeKey] =
          newValue[
            changeKey as keyof {
              name: string;
              description: string;
            }
          ] ?? "";
      });
      const updated = (
        await db.update(roles).set(payload).where(eq(roles.id, id)).returning()
      ).at(0);

      if (!updated) throw new Error("No role returned");
      return { data: updated, error: undefined };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to update role" },
      };
    }
  }

  async function deleteRoleById(id: string) {
    try {
      const rows = await db.delete(roles).where(eq(roles.id, id));
      return {
        data: { rows: rows.count },
        error: undefined,
      };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to delete role" },
      };
    }
  }

  return { getRoles, createRole, getRoleById, updateRoleById, deleteRoleById };
}
