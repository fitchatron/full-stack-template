import { z } from "zod";
import { timestamps, userMetadata } from "@validators/validator.helpers";

export const roleSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  description: z.string().min(1).max(255),
  ...timestamps,
  ...userMetadata,
});

export const addRoleSchema = roleSchema.pick({
  name: true,
  description: true,
  createdBy: true,
  modifiedBy: true,
});

export const updateRoleSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().min(1).max(255).optional(),
});
