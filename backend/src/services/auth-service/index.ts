import { Request } from "express";
import { cryptoService } from "@utils/crypto";
import { db } from "@db/db";
import { users } from "@db/schema";
import { signUpUserSchema, signInUserSchema } from "@validators/auth";
import { eventLogger } from "@utils/logger";
import { eq } from "drizzle-orm";

export function authService() {
  const { generateSaltAndHash, compareValueToHash } = cryptoService();

  async function signUpUser(req: Request) {
    try {
      const result = signUpUserSchema.safeParse({
        ...req.body,
      });
      if (!result.success) {
        const fieldErrors = result.error.flatten().fieldErrors;
        const validationErrors = Object.entries(fieldErrors).map(
          ([field, errors]) => {
            return `${field}: ${errors.join("\n")}`;
          },
        );
        return {
          data: undefined,
          error: {
            code: 400,
            message: `Failed to Create user. Missing or invalid data. ${validationErrors}`,
          },
        };
      }

      // Hash password
      const { salt, hash } = await generateSaltAndHash(result.data.password);

      const user = (
        await db
          .insert(users)
          .values({
            firstName: result.data.firstName,
            lastName: result.data.lastName,
            email: result.data.email,
            passwordHash: hash,
            salt: salt,
          })
          .returning()
      ).at(0);
      if (!user) throw new Error("No user returned");
      return { data: user, error: undefined };
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create user" },
      };
    }
  }

  async function signInUser(req: Request) {
    try {
      const result = signInUserSchema.safeParse({
        ...req.body,
      });

      if (!result.success) return failedSignInHelper();

      const user = await db.query.users.findFirst({
        where: eq(users.email, result.data.email),
      });

      if (!user) return failedSignInHelper();

      const match = await compareValueToHash(
        result.data.password,
        user.passwordHash,
        { hashWithpepper: true },
      );

      if (!match) return failedSignInHelper();

      return { data: user, error: undefined };
    } catch (error) {
      const { logEvent } = eventLogger({
        type: "error",
        message: `${error}`,
      });
      logEvent();
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create user" },
      };
    }
  }

  function failedSignInHelper() {
    return {
      data: undefined,
      error: {
        code: 401,
        message: `Failed to sign in`,
      },
    };
  }
  return {
    signUpUser,
    signInUser,
  };
}
