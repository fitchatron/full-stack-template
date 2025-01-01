import { z } from "zod";
import { timestamps, userMetadata } from "@validators/validator.helpers";

export const permissionSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(255),
  description: z.string().min(1).max(255),
  ...timestamps,
  ...userMetadata,
});

export const addPermissionSchema = permissionSchema.pick({
  name: true,
  description: true,
  createdBy: true,
  modifiedBy: true,
});

export const updatePermissionSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().min(1).max(255).optional(),
});
