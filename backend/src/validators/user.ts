import { z } from "zod";
import { timestamps, userMetadata } from "@validators/validator.helpers";

export const userSchema = z.object({
  id: z.string().uuid(),
  firstName: z
    .string({ required_error: "User's first name is required" })
    .min(1)
    .max(255),
  lastName: z
    .string({ required_error: "User's last name is required" })
    .min(1)
    .max(255),
  email: z.string({ required_error: "User's email is required" }).email(),
  passwordHash: z.string({ required_error: "User's password is required" }),
  ...timestamps,
  ...userMetadata,
});

export const updateUserSchema = z.object({
  firstName: z.string().min(1).max(255).optional(),
  lastName: z.string().min(1).max(255).optional(),
  email: z.string().email().optional(),
});
