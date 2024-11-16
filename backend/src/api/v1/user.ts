import express, { Request, Response } from "express";
import { db } from "@db/db";
import { users } from "@db/schema";
import { addUserSchema } from "@validators/user";
import { eventLogger } from "@utils/logger";
import { type PaginatedResponse } from "@models/pagination";

const app = express();

app.get("/", async (req: Request, res: Response) => {
  try {
    const page = parseInt(req.query.page?.toString() ?? "1");
    const limit = parseInt(req.query.limit?.toString() ?? "10");

    const startIndex = (page - 1) * limit;
    const total = await db.$count(users);
    const pages = Math.ceil(total / limit);
    const result = await db
      .select()
      .from(users)
      .offset(startIndex)
      .limit(limit);

    const payload: PaginatedResponse<{
      id: string;
      firstName: string;
      lastName: string;
      email: string;
      createdBy: string | null;
      updatedBy: string | null;
      createdAt: Date;
      updatedAt: Date;
    }> = {
      items: result,
      metadata: {
        limit,
        page,
        pages,
        total,
      },
    };
    res.status(200).send(payload);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to fetch users" });
  }
});

app.post("/", async (req: Request, res: Response) => {
  try {
    const body = req.body;
    console.log("BODY", body);
    const result = addUserSchema.safeParse(body);
    if (!result.success) {
      throw result.error;
    }
    console.log("validation passed");

    const user = await db.insert(users).values(result.data).returning();
    res.status(201).send(user);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to create user" });
  }
});

app.get("/:userId", (req: Request, res: Response) => {
  const userId = req.params.userId;
  res.send(`Get user by Id ${userId}`);
  return;
});

app.put("/:userId", (req: Request, res: Response) => {
  const userId = req.params.userId;
  res.send(`Update user by Id ${userId}`);
  return;
});

app.delete("/:userId", (req: Request, res: Response) => {
  const userId = req.params.userId;
  res.send(`Delete user by Id ${userId}`);
  return;
});

export default app;
