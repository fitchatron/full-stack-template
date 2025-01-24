import { Request } from "express";
import { db } from "@db/db";
import { withPagination } from "@db/utils";
import { users, permissions } from "@db/schema";
import { asc, eq } from "drizzle-orm";
import { eventLogger } from "@utils/logger";
import {
  addPermissionSchema,
  updatePermissionSchema,
} from "@validators/permission";
import { parseZodErrorToResponse } from "@utils/error";

export function permissionService() {
  async function getPermissions(req: Request) {
    try {
      const page = parseInt(req.query.page?.toString() ?? "1");
      const limit = parseInt(req.query.limit?.toString() ?? "10");

      const query = db.select().from(permissions);

      const payload = await withPagination(
        query.$dynamic(),
        asc(permissions.id),
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

  async function createPermission(req: Request) {
    try {
      const result = addPermissionSchema.safeParse(req.body);
      if (!result.success) {
        return parseZodErrorToResponse(result.error);
      }
      const permission = await db
        .insert(permissions)
        .values(result.data)
        .returning();

      return { data: permission, error: undefined };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create permission" },
      };
    }
  }

  async function getPermissionById(id: string) {
    try {
      const permission = await db.query.permissions.findFirst({
        where: eq(permissions.id, id),
      });

      if (!permission) {
        return {
          data: undefined,
          error: { code: 404, message: "Unable to get permission" },
        };
      }

      return {
        data: permission,
        error: undefined,
      };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to get permission" },
      };
    }
  }

  async function updatePermissionById(
    id: string,
    body: Record<string, string>,
  ) {
    try {
      const { data: currentValue, error } = await getPermissionById(id);

      if (error) {
        return {
          data: undefined,
          error: error,
        };
      }

      const result = updatePermissionSchema.safeParse(body);
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
        throw new Error("No Changes to permission");
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
        await db.update(users).set(payload).where(eq(users.id, id)).returning()
      ).at(0);

      if (!updated) throw new Error("No permission returned");
      return { data: updated, error: undefined };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to update permission" },
      };
    }
  }

  async function deletePermissionById(id: string) {
    try {
      const rows = await db.delete(permissions).where(eq(permissions.id, id));
      return {
        data: rows.count,
        error: undefined,
      };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to delete permission" },
      };
    }
  }

  return {
    getPermissions,
    createPermission,
    getPermissionById,
    updatePermissionById,
    deletePermissionById,
  };
}
