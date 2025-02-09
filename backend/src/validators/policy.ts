import { z } from "zod";
import { timestamps, userMetadata } from "@validators/validator.helpers";

export const policySchema = z.object({
  id: z.string().uuid(),
  resource: z.string().min(1).max(255),
  action: z.enum(["view", "edit", "create", "delete"]),
  condition: z
    .string()
    .refine(
      (val) => {
        try {
          JSON.parse(val);
          return true;
        } catch {
          return false;
        }
      },
      {
        message: "Condition muse be valid JSON.",
      },
    )
    .optional(),
  decision: z.enum(["allow", "deny"]),
  ...timestamps,
  ...userMetadata,
});

export const addPolicySchema = policySchema.pick({
  resource: true,
  action: true,
  condition: true,
  decision: true,
  createdBy: true,
  modifiedBy: true,
});

export const updatePolicySchema = z.object({
  resource: z.string().min(1).max(255).optional(),
  action: z.enum(["view", "edit", "create", "delete"]).optional(),
  condition: z
    .string()
    .refine(
      (val) => {
        try {
          JSON.parse(val);
          return true;
        } catch {
          return false;
        }
      },
      {
        message: "Condition muse be valid JSON.",
      },
    )
    .optional(),
  decision: z.enum(["allow", "deny"]).optional(),
});
