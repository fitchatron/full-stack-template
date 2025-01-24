import { db } from "@db/db";
import { userRoles } from "@db/schema";
import { parseZodErrorToResponse } from "@utils/error";
import { eventLogger } from "@utils/logger";
import { addUserRoleSchema } from "@validators/user-roles";
import { and, eq } from "drizzle-orm";

export function userRoleService() {
  async function createUserRole(
    userId: string,
    payload: Record<string, string>,
  ) {
    try {
      const result = addUserRoleSchema.safeParse({ payload, userId });

      if (!result.success) {
        return parseZodErrorToResponse(result.error);
      }
      const userRole = await db
        .insert(userRoles)
        .values(result.data)
        .returning();
      return { data: userRole, error: undefined };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create user role" },
      };
    }
  }

  async function deleteUserRole(userId: string, roleId: string) {
    try {
      const rows = await db
        .delete(userRoles)
        .where(and(eq(userRoles.userId, userId), eq(userRoles.roleId, roleId)));

      return {
        data: rows.count,
        error: undefined,
      };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to delete user role" },
      };
    }
  }

  return { createUserRole, deleteUserRole };
}
