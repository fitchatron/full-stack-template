import express, { Request, Response } from "express";
import { db } from "@db/db";
import { userRoles } from "@db/schema";
import { eventLogger } from "@utils/logger";
import { and, eq } from "drizzle-orm";
import { addUserRoleSchema } from "@validators/user-roles";
import { userService } from "@services/user-service";

const app = express();
const service = userService();

/**
 * @swagger
 * tags:
 *   name: Users
 *   description: User management and retrieval
 */

/**
 * @openapi
 * /api/v1/users:
 *   get:
 *     summary: Retrieve list of users
 *     description: Get a paginated list of users.
 *     tags: [Users]
 *     responses:
 *       200:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              type: object
 *              properties:
 *                items:
 *                  type: array
 *                  items:
 *                    $ref: '#/components/schemas/User'
 *                metadata:
 *                    $ref: '#/components/schemas/PaginatedMetadata'
 *                links:
 *                    $ref: '#/components/schemas/PaginatedLinks'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 */
app.get("/", async (req: Request, res: Response) => {
  const { data, error } = await service.getUsers(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
});

/**
 * @openapi
 * /api/v1/users:
 *   post:
 *     summary: Create a new user
 *     description: Create a new user from the payload
 *     tags: [Users]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - firstName
 *               - lastName
 *               - email
 *             properties:
 *               firstName:
 *                 type: string
 *               lastName:
 *                 type: string
 *               email:
 *                 type: string
 *                 format: email
 *                 description: must be unique
 *             example:
 *               firstName: John
 *               lastName: Doe
 *               email: john.doe@example.com
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/User'
 *       400:
 *         $ref: '#/components/responses/DuplicateEmail'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *
 */
app.post("/", async (req: Request, res: Response) => {
  const { data, error } = await service.createUser(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(201).send(data);
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
