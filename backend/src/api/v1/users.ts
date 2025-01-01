import express, { Request, Response } from "express";
import { db } from "@db/db";
import { users } from "@db/schema";
import { addUserSchema, updateUserSchema } from "@validators/user";
import { eventLogger } from "@utils/logger";
import { asc, eq } from "drizzle-orm";
import { withPagination } from "@db/utils";

const app = express();

app.get("/", async (req: Request, res: Response) => {
  try {
    const page = parseInt(req.query.page?.toString() ?? "1");
    const limit = parseInt(req.query.limit?.toString() ?? "10");

    const query = db.select().from(users);

    const payload = await withPagination(
      query.$dynamic(),
      asc(users.id),
      page,
      limit,
      req,
    );
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
    const result = addUserSchema.safeParse(req.body);
    if (!result.success) {
      throw result.error;
    }
    const user = await db.insert(users).values(result.data).returning();
    res.status(201).send(user);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to create user" });
  }
});

app.get("/:userId", async (req: Request, res: Response) => {
  try {
    const userId = req.params.userId;

    const user = await getUserById(userId);

    if (!user) {
      res.status(404).send({ message: "Unable to get user" });
      return;
    }
    res.status(200).send(user);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to get user" });
  }
});

app.put("/:userId", async (req: Request, res: Response) => {
  try {
    const userId = req.params.userId;
    const currentValue = await getUserById(userId);
    if (!currentValue) {
      res.status(404).send({ message: "Unable to get user" });
      return;
    }

    const result = updateUserSchema.safeParse(req.body);
    if (!result.success) {
      throw result.error;
    }
    const newValue = result.data;
    const changes = new Set<string>();
    Object.entries(newValue).forEach(([key, value]) => {
      if (
        currentValue[
          key as keyof {
            firstName: string;
            lastName: string;
            email: string;
          }
        ] !== value
      ) {
        changes.add(key);
      }
    });

    if (changes.size === 0) {
      throw new Error("No Changes to user");
    }
    const payload: Record<string, number | string | Date | boolean> = {
      updatedAt: new Date(),
      // updatedBy: userId,
    };
    changes.forEach((changeKey) => {
      payload[changeKey] =
        newValue[
          changeKey as keyof {
            firstName: string;
            lastName: string;
            email: string;
          }
        ] ?? "";
    });
    const updated = await db
      .update(users)
      .set(payload)
      .where(eq(users.id, userId))
      .returning();
    res.status(200).send(updated);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to update user" });
  }
});

app.delete("/:userId", async (req: Request, res: Response) => {
  try {
    const userId = req.params.userId;
    const rows = await db.delete(users).where(eq(users.id, userId));
    res.status(200).send({ success: true, rows: rows.count });
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to delete user" });
  }
});

async function getUserById(id: string) {
  return db.query.users.findFirst({
    where: eq(users.id, id),
  });
}

export default app;
