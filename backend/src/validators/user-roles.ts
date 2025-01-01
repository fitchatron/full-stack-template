import { z } from "zod";
import { timestamps, userMetadata } from "@validators/validator.helpers";

export const userRoleSchema = z.object({
  userId: z.string().uuid(),
  roleId: z.string().uuid(),
  ...timestamps,
  ...userMetadata,
});

export const addUserRoleSchema = userRoleSchema.pick({
  userId: true,
  roleId: true,
  createdBy: true,
  modifiedBy: true,
});
