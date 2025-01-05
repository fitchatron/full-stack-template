import express, { Request, Response } from "express";
import { db } from "@db/db";
import { userRoles } from "@db/schema";
import { eventLogger } from "@utils/logger";
import { and, eq } from "drizzle-orm";
import { addUserRoleSchema } from "@validators/user-roles";
import { userService } from "@services/user-service";

const app = express();
const service = userService();

app.get("/", async (req: Request, res: Response) => {
  const { data, error } = await service.getUsers(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
});

app.post("/", async (req: Request, res: Response) => {
  const { data, error } = await service.createUser(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
});

app.get("/:userId", async (req: Request, res: Response) => {
  try {
    const userId = req.params.userId;

    const { data, error } = await service.getUserById(userId);

    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
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
    const { data, error } = await service.updateUserById(userId, req.body);
    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
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
    const { data, error } = await service.deleteUserById(userId);
    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to delete user" });
  }
});

app.post("/:userId/roles", async (req: Request, res: Response) => {
  try {
    const roleId = req.params.roleId;
    const result = addUserRoleSchema.safeParse({ ...req.body, roleId });

    if (!result.success) {
      throw result.error;
    }
    const userRole = await db.insert(userRoles).values(result.data).returning();
    res.status(201).send(userRole);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to create user role" });
  }
});

app.delete("/:userId/roles/:roleId", async (req: Request, res: Response) => {
  try {
    const userId = req.params.userId;
    const roleId = req.params.roleId;
    const rows = await db
      .delete(userRoles)
      .where(and(eq(userRoles.userId, userId), eq(userRoles.roleId, roleId)));

    res.status(200).send({ success: true, rows: rows.count });
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to delete user role" });
  }
});

export default app;
