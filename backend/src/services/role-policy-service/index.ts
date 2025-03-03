import { db } from "@db/db";
import { rolePolicies } from "@db/schema";
import { parseZodErrorToResponse } from "@utils/error";
import { eventLogger } from "@utils/logger";
import { addRolePolicySchema } from "@validators/role-policy";
import { and, eq } from "drizzle-orm";

export function rolePolicyService() {
  const { logEvent } = eventLogger();

  async function createRolePolicy(
    roleId: string,
    payload: Record<string, string>,
  ) {
    try {
      const result = addRolePolicySchema.safeParse({ ...payload, roleId });

      if (!result.success) {
        return parseZodErrorToResponse(result.error);
      }
      const rolePolicy = await db
        .insert(rolePolicies)
        .values(result.data)
        .returning();
      return { data: rolePolicy, error: undefined };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create role policy" },
      };
    }
  }

  async function deleteRolePolicy(roleId: string, policyId: string) {
    try {
      const rows = await db
        .delete(rolePolicies)
        .where(
          and(
            eq(rolePolicies.roleId, roleId),
            eq(rolePolicies.policyId, policyId),
          ),
        );

      return {
        data: { rows: rows.count },
        error: undefined,
      };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to delete role policy" },
      };
    }
  }

  return { createRolePolicy, deleteRolePolicy };
}
