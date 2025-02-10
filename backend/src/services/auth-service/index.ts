import { Request, Response } from "express";
import { cryptoService } from "@utils/crypto";
import { db } from "@db/db";
import { sessions, users } from "@db/schema";
import { signUpUserSchema, signInUserSchema } from "@validators/auth";
import { eventLogger } from "@utils/logger";
import { eq } from "drizzle-orm";
import { randomBytes } from "crypto";
import { APP_CONFIG } from "@utils/config/app.config";
import { userService } from "@services/user-service";

export function authService() {
  const { generateSaltAndHash, compareValueToHash } = cryptoService();
  const { logEvent } = eventLogger();

  async function signUpUser(req: Request, res: Response) {
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

      const { assignRoleTo } = userService();
      await assignRoleTo(user.id, "public", user.id);
      const session = await createSession(req, user.id);
      // Set cookie
      res.cookie("session", session.token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        expires: session.expiresAt,
      });
      return { data: user, error: undefined };
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      return {
        data: undefined,
        error: { code: 500, message: "Unable to create user" },
      };
    }
  }

  async function signInUser(req: Request, res: Response) {
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

      const session = await createSession(req, user.id);
      // Set cookie
      res.cookie("session", session.token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        expires: session.expiresAt,
      });
      return { data: user, error: undefined };
    } catch (error) {
      logEvent({
        type: "error",
        message: `${error}`,
      });
      return failedSignInHelper();
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

  async function createSession(req: Request, userId: string) {
    const ipAddress = `${req.ip || req.headers["x-forwarded-for"] || req.socket.remoteAddress}`;
    // Hash password
    const { hash } = await generateSaltAndHash(ipAddress);
    const userAgent = req.headers["user-agent"];
    const token = randomBytes(32).toString("hex");
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 30); // 30 days from now

    const session = (
      await db
        .insert(sessions)
        .values({
          token,
          userId,
          ipAddress: APP_CONFIG.hashValues ? hash : ipAddress,
          userAgent,
          expiresAt,
        })
        .returning()
    ).at(0);

    if (!session) throw new Error("Failed to create session");
    return session;
  }

  return {
    signUpUser,
    signInUser,
  };
}
