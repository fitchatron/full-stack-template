import { z } from "zod";
import { timestamps, userMetadata } from "@validators/validator.helpers";

export const rolePolicySchema = z.object({
  roleId: z.string().uuid(),
  policyId: z.string().uuid(),
  ...timestamps,
  ...userMetadata,
});

export const addRolePolicySchema = rolePolicySchema.pick({
  roleId: true,
  policyId: true,
  createdBy: true,
  modifiedBy: true,
});
