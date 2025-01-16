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
 * /api/v1/users/{userId}:
 *   get:
 *     summary: Get a user
 *     description: Get a user by ID
 *     tags: [Users]
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *         description: User ID
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/User'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *
 */
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

/**
 * @openapi
 * /api/v1/users/{userId}:
 *   put:
 *     summary: Update a user
 *     description: Update a user
 *     tags: [Users]
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *         description: User ID
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
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *
 */
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

/**
 * @openapi
 * /api/v1/users/{userId}:
 *   delete:
 *     summary: Delete a user
 *     description: Logged in users can delete only themselves. Only admins can delete other users.
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *         description: User ID
 *     responses:
 *       "200":
 *         description: Number of rows deleted
 *       "401":
 *         $ref: '#/components/responses/Unauthorized'
 *       "403":
 *         $ref: '#/components/responses/Forbidden'
 *       "404":
 *         $ref: '#/components/responses/NotFound'
 */
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

/**
 *
 * @openapi
 * /api/v1/users/{userId}/roles:
 *   post:
 *     summary: Create a new user role
 *     description: Create a new user role for the given user
 *     tags: [Users]
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *         description: User ID
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - userId
 *               - roleId
 *               - createdBy
 *               - modifiedBy
 *             properties:
 *               userId:
 *                 type: string
 *               roleId:
 *                 type: string
 *               createdBy:
 *                 type: string
 *                 format: date-time
 *               modifiedBy:
 *                 type: string
 *                 format: date-time
 *             example:
 *               userId: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *               roleId: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *               createdBy: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *               modifiedBy: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/UserRole'
 *       400:
 *         $ref: '#/components/responses/DuplicateEntity'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *
 */
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

/**
 * @openapi
 * /api/v1/users/{userId}/roles/{roleId}:
 *   delete:
 *     summary: Delete a user role
 *     description: Deletes a user role given a user ID and role ID
 *     tags: [Users]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *         description: User ID
 *       - in: path
 *         name: roleId
 *         required: true
 *         schema:
 *           type: string
 *         description: Role ID
 *     responses:
 *       "200":
 *         description: Number of rows deleted
 *       "401":
 *         $ref: '#/components/responses/Unauthorized'
 *       "403":
 *         $ref: '#/components/responses/Forbidden'
 *       "404":
 *         $ref: '#/components/responses/NotFound'
 */
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
