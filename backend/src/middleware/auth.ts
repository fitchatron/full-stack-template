import { db } from "@db/db";
import { sessions } from "@db/schema";
import { cryptoService } from "@utils/crypto";
import { and, eq } from "drizzle-orm";
import { Request, Response, NextFunction } from "express";

export async function requireAuth(
  req: Request,
  res: Response,
  next: NextFunction,
) {
  try {
    const { generateSaltAndHash } = cryptoService();
    const token = req.cookies.session;

    const ipAddress = `${req.ip || req.headers["x-forwarded-for"] || req.socket.remoteAddress}`;
    // Hash password
    const { hash: hashIpAddress } = await generateSaltAndHash(ipAddress);
    const userAgent = req.headers["user-agent"] ?? "";
    if (!token) {
      res.status(401).json({ error: "Authentication required" });
      return;
    }

    const session = await db.query.sessions.findFirst({
      with: { user: true },
      where: and(
        eq(sessions.token, token),
        eq(sessions.ipAddress, hashIpAddress),
        eq(sessions.userAgent, userAgent),
        // lt(sessions.expiresAt, new Date()),
      ),
    });

    if (!session) {
      res.clearCookie("session");
      res.status(401).json({ error: "Invalid session" });
      return;
    }

    if (session.expiresAt < new Date()) {
      await db.delete(sessions).where(eq(sessions.id, session.id));
      res.clearCookie("session");
      res.status(401).json({ error: "Session expired" });
      return;
    }

    req.user = {
      id: session.user.id,
      firstName: session.user.firstName,
      lastName: session.user.lastName,
      email: session.user.email,
    };
    req.session = {
      id: session.id,
      token: session.token,
    };

    next();
  } catch (error) {
    console.error("Auth middleware error:", error);
    res.status(500).json({ error: "Internal server error" });
  }
}
