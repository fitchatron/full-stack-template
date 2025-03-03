import { Request } from "express";
import { db } from "@db/db";
import { withPagination } from "@db/utils";
import { policies } from "@db/schema";
import { asc, eq } from "drizzle-orm";
import { eventLogger } from "@utils/logger";
import { addPolicySchema, updatePolicySchema } from "@validators/policy";
import { parseZodErrorToResponse } from "@utils/error";

export function policyService() {
  const { logEvent } = eventLogger();

  async function getPolicies(req: Request) {
    try {
      const page = parseInt(req.query.page?.toString() ?? "1");
      const limit = parseInt(req.query.limit?.toString() ?? "10");

      const query = db.select().from(policies);

      const payload = await withPagination(
        query.$dynamic(),
        asc(policies.id),
        page,
        limit,
        req,
      );

      return { data: payload, error: undefined };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to fetch policies" },
      };
    }
  }

  async function createPolicy(req: Request) {
    try {
      const result = addPolicySchema.safeParse(req.body);
      if (!result.success) {
        return parseZodErrorToResponse(result.error);
      }
      const policy = await db.insert(policies).values(result.data).returning();

      return { data: policy, error: undefined };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create policy" },
      };
    }
  }

  async function getPolicyById(id: string) {
    try {
      const policy = await db.query.policies.findFirst({
        where: eq(policies.id, id),
      });

      if (!policy) {
        return {
          data: undefined,
          error: { code: 404, message: "Unable to get policy" },
        };
      }

      return {
        data: policy,
        error: undefined,
      };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to get policy" },
      };
    }
  }

  async function updatePolicyById(id: string, body: Record<string, string>) {
    try {
      const { data: currentValue, error } = await getPolicyById(id);

      if (error) {
        return {
          data: undefined,
          error: error,
        };
      }

      const result = updatePolicySchema.safeParse(body);
      if (!result.success) {
        throw result.error;
      }
      const newValue = result.data;
      const changes = new Set<string>();
      Object.entries(newValue).forEach(([key, value]) => {
        if (
          currentValue[
            key as keyof {
              resource: string;
              action: "view" | "edit" | "create" | "delete";
              condition: string;
              decision: "allow" | "deny";
            }
          ] !== value
        ) {
          changes.add(key);
        }
      });

      if (changes.size === 0) {
        throw new Error("No Changes to policy");
      }
      const payload: Record<string, number | string | Date | boolean> = {
        updatedAt: new Date(),
        // updatedBy: userId,
      };
      changes.forEach((changeKey) => {
        payload[changeKey] =
          newValue[
            changeKey as keyof {
              resource: string;
              action: "view" | "edit" | "create" | "delete";
              condition: string;
              decision: "allow" | "deny";
            }
          ] ?? "";
      });
      const updated = (
        await db
          .update(policies)
          .set(payload)
          .where(eq(policies.id, id))
          .returning()
      ).at(0);

      if (!updated) throw new Error("No policy returned");
      return { data: updated, error: undefined };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to update policy" },
      };
    }
  }

  async function deletePolicyById(id: string) {
    try {
      const rows = await db.delete(policies).where(eq(policies.id, id));
      return {
        data: { rows: rows.count },
        error: undefined,
      };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to delete policy" },
      };
    }
  }

  return {
    getPolicies,
    createPolicy,
    getPolicyById,
    updatePolicyById,
    deletePolicyById,
  };
}
