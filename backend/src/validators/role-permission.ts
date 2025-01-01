import { z } from "zod";
import { timestamps, userMetadata } from "@validators/validator.helpers";

export const rolePermissionSchema = z.object({
  roleId: z.string().uuid(),
  permissionId: z.string().uuid(),
  ...timestamps,
  ...userMetadata,
});

export const addRolePermissionSchema = rolePermissionSchema.pick({
  roleId: true,
  permissionId: true,
  createdBy: true,
  modifiedBy: true,
});
