import { z } from "zod";
import { timestamps, userMetadata } from "@validators/validator.helpers";

export const userSchema = z.object({
  id: z.string().uuid(),
  firstName: z.string().min(1).max(255),
  lastName: z.string().min(1).max(255),
  email: z.string().email(),
  ...timestamps,
  ...userMetadata,
});

export const addUserSchema = userSchema.pick({
  firstName: true,
  lastName: true,
  email: true,
  createdBy: true,
  modifiedBy: true,
});
