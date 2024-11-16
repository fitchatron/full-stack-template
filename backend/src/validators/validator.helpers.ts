import { z } from "zod";

export const timestamps = {
  createdAt: z.string().datetime(),
  modifiedAt: z.string().datetime(),
};

export const userMetadata = {
  createdBy: z.string().uuid().optional(),
  modifiedBy: z.string().uuid().optional(),
};
