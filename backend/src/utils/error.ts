import { ZodError } from "zod";

export function parseZodErrorToResponse<T>(error: ZodError<T>) {
  const fieldErrors = error.flatten().fieldErrors;
  const validationErrors = Object.entries(fieldErrors).map(
    ([field, errors]) => {
      return `${field}: ${(errors as string[]).join("\n")}`;
    },
  );
  return {
    data: undefined,
    error: {
      code: 400,
      message: `Failed to Create item. Missing or invalid data. ${validationErrors}`,
    },
  };
}
