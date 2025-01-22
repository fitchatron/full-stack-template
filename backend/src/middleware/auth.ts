import { db } from "@db/db";
import { sessions } from "@db/schema";
import { eq } from "drizzle-orm";
import { Request, Response, NextFunction } from "express";

export async function requireAuth(
  req: Request,
  res: Response,
  next: NextFunction,
) {
  try {
    const token = req.cookies.session;

    if (!token) {
      res.status(401).json({ error: "Authentication required" });
      return;
    }

    const session = await db.query.sessions.findFirst({
      with: { user: true },
      where: eq(sessions.token, token),
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
