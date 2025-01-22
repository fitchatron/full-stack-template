import { Request, Response, Router } from "express";
import { db } from "@db/db";
import { eventLogger } from "@utils/logger";
import { and, asc, eq } from "drizzle-orm";
import { roles, rolePermissions } from "@db/schema";
import { withPagination } from "@db/utils";
import { addRoleSchema, updateRoleSchema } from "@validators/role";
import { addRolePermissionSchema } from "@validators/role-permission";

const router = Router();

/**
 * @openapi
 * /api/v1/roles:
 *   get:
 *     summary: Retrieve list of roles
 *     description: Get a paginated list of roles.
 *     tags: [Roles]
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
 *                    $ref: '#/components/schemas/Role'
 *                metadata:
 *                    $ref: '#/components/schemas/PaginatedMetadata'
 *                links:
 *                    $ref: '#/components/schemas/PaginatedLinks'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 */
router.get("/", async (req: Request, res: Response) => {
  try {
    const page = parseInt(req.query.page?.toString() ?? "1");
    const limit = parseInt(req.query.limit?.toString() ?? "10");

    const query = db.select().from(roles);

    const payload = await withPagination(
      query.$dynamic(),
      asc(roles.id),
      page,
      limit,
      req,
    );

    res.status(200).send(payload);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to fetch roles" });
  }
});

/**
 * @openapi
 * /api/v1/roles:
 *   post:
 *     summary: Create a new role
 *     description: Create a new role from the payload
 *     tags: [Roles]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - name
 *               - description
 *             properties:
 *               name:
 *                 type: string
 *                 description: must be unique
 *               description:
 *                 type: string
 *             example:
 *               name: public
 *               description: Default role for users of the router.
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/Role'
 *       400:
 *         $ref: '#/components/responses/DuplicateEntity'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *
 */
router.post("/", async (req: Request, res: Response) => {
  try {
    const result = addRoleSchema.safeParse(req.body);
    if (!result.success) {
      throw result.error;
    }
    const role = await db.insert(roles).values(result.data).returning();
    res.status(201).send(role);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to create role" });
  }
});

/**
 * @openapi
 * /api/v1/roles/{roleId}:
 *   get:
 *     summary: Get a role
 *     description: Get a role by ID
 *     tags: [Roles]
 *     parameters:
 *       - in: path
 *         name: roleId
 *         required: true
 *         schema:
 *           type: string
 *         description: Role ID
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/Role'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *
 */
router.get("/:roleId", async (req: Request, res: Response) => {
  try {
    const roleId = req.params.roleId;

    const role = await getRoleById(roleId);

    if (!role) {
      res.status(404).send({ message: "Unable to get role" });
      return;
    }
    res.status(200).send(role);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to get role" });
  }
});

/**
 * @openapi
 * /api/v1/roles/{roleId}:
 *   put:
 *     summary: Update a role
 *     description: Update a role
 *     tags: [Roles]
 *     parameters:
 *       - in: path
 *         name: roleId
 *         required: true
 *         schema:
 *           type: string
 *         description: Role ID
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - name
 *               - description
 *             properties:
 *               name:
 *                 type: string
 *                 description: must be unique
 *               description:
 *                 type: string
 *             example:
 *               name: public
 *               description: Default role for users of the router.
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
router.put("/:roleId", async (req: Request, res: Response) => {
  try {
    const roleId = req.params.roleId;
    const currentValue = await getRoleById(roleId);
    if (!currentValue) {
      res.status(404).send({ message: "Unable to get role" });
      return;
    }

    const result = updateRoleSchema.safeParse(req.body);
    if (!result.success) {
      throw result.error;
    }
    const newValue = result.data;
    const changes = new Set<string>();
    Object.entries(newValue).forEach(([key, value]) => {
      if (
        currentValue[
          key as keyof {
            name: string;
            description: string;
          }
        ] !== value
      ) {
        changes.add(key);
      }
    });

    if (changes.size === 0) {
      throw new Error("No Changes to role");
    }
    const payload: Record<string, number | string | Date | boolean> = {
      updatedAt: new Date(),
      // updatedBy: roleId,
    };
    changes.forEach((changeKey) => {
      payload[changeKey] =
        newValue[
          changeKey as keyof {
            name: string;
            description: string;
          }
        ] ?? "";
    });

    const updated = await db
      .update(roles)
      .set(payload)
      .where(eq(roles.id, roleId))
      .returning();
    res.status(200).send(updated);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to update role" });
  }
});

/**
 * @openapi
 * /api/v1/roles/{roleId}:
 *   delete:
 *     summary: Delete a role
 *     description: Only admins can delete roles.
 *     tags: [Roles]
 *     security:
 *       - bearerAuth: []
 *     parameters:
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
router.delete("/:roleId", async (req: Request, res: Response) => {
  try {
    const roleId = req.params.roleId;
    const rows = await db.delete(roles).where(eq(roles.id, roleId));
    res.status(200).send({ success: true, rows: rows.count });
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to delete role" });
  }
});

/**
 *
 * @openapi
 * /api/v1/roles/{roleId}/permissions:
 *   post:
 *     summary: Create a new role permission
 *     description: Create a new role permission for the given role
 *     tags: [Roles]
 *     parameters:
 *       - in: path
 *         name: roleId
 *         required: true
 *         schema:
 *           type: string
 *         description: Role ID
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - roleId
 *               - permissionId
 *               - createdBy
 *               - modifiedBy
 *             properties:
 *               roleId:
 *                 type: string
 *               permissionId:
 *                 type: string
 *               createdBy:
 *                 type: string
 *                 format: date-time
 *               modifiedBy:
 *                 type: string
 *                 format: date-time
 *             example:
 *               roleId: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *               permissionId: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *               createdBy: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *               modifiedBy: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/RolePermission'
 *       400:
 *         $ref: '#/components/responses/DuplicateEntity'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *
 */
router.post("/:roleId/permissions", async (req: Request, res: Response) => {
  try {
    const roleId = req.params.roleId;
    const result = addRolePermissionSchema.safeParse({ ...req.body, roleId });

    if (!result.success) {
      throw result.error;
    }
    const rolePermission = await db
      .insert(rolePermissions)
      .values(result.data)
      .returning();
    res.status(201).send(rolePermission);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to create role permission" });
  }
});

/**
 * @openapi
 * /api/v1/roles/{roleId}/permissions/{permissionId}:
 *   delete:
 *     summary: Delete a role permission
 *     description: Deletes a role permission given a role ID and permission ID
 *     tags: [Roles]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: roleId
 *         required: true
 *         schema:
 *           type: string
 *         description: Role ID
 *       - in: path
 *         name: permissionId
 *         required: true
 *         schema:
 *           type: string
 *         description: Permission ID
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
router.delete(
  "/:roleId/permissions/:permissionId",
  async (req: Request, res: Response) => {
    try {
      const roleId = req.params.roleId;
      const permissionId = req.params.permissionId;
      const rows = await db
        .delete(rolePermissions)
        .where(
          and(
            eq(rolePermissions.roleId, roleId),
            eq(rolePermissions.permissionId, permissionId),
          ),
        );

      res.status(200).send({ success: true, rows: rows.count });
      return;
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      res.status(500).send({ message: "Unable to delete role permission" });
    }
  },
);

async function getRoleById(id: string) {
  return db.query.roles.findFirst({
    where: eq(roles.id, id),
  });
}

export default router;
