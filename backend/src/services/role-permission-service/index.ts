import { db } from "@db/db";
import { rolePermissions } from "@db/schema";
import { parseZodErrorToResponse } from "@utils/error";
import { eventLogger } from "@utils/logger";
import { addRolePermissionSchema } from "@validators/role-permission";
import { and, eq } from "drizzle-orm";

export function rolePermissionService() {
  async function createRolePermission(
    roleId: string,
    payload: Record<string, string>,
  ) {
    try {
      const result = addRolePermissionSchema.safeParse({ ...payload, roleId });

      if (!result.success) {
        return parseZodErrorToResponse(result.error);
      }
      const rolePermission = await db
        .insert(rolePermissions)
        .values(result.data)
        .returning();
      return { data: rolePermission, error: undefined };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create user role" },
      };
    }
  }

  async function deleteRolePermission(roleId: string, permissionId: string) {
    try {
      const rows = await db
        .delete(rolePermissions)
        .where(
          and(
            eq(rolePermissions.roleId, roleId),
            eq(rolePermissions.permissionId, permissionId),
          ),
        );

      return {
        data: rows.count,
        error: undefined,
      };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to delete role permission" },
      };
    }
  }

  return { createRolePermission, deleteRolePermission };
}
