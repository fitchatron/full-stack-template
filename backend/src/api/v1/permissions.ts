import { Request, Response, Router } from "express";
import { db } from "@db/db";
import { eventLogger } from "@utils/logger";
import { asc, eq } from "drizzle-orm";
import { withPagination } from "@db/utils";
import { permissions } from "@db/schema";
import {
  addPermissionSchema,
  updatePermissionSchema,
} from "@validators/permission";

const router = Router();

/**
 * @openapi
 * /api/v1/permissions:
 *   get:
 *     summary: Retrieve list of permissions
 *     description: Get a paginated list of permissions.
 *     tags: [Permissions]
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
 *                    $ref: '#/components/schemas/Permission'
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

    const query = db.select().from(permissions);

    const payload = await withPagination(
      query.$dynamic(),
      asc(permissions.id),
      page,
      limit,
      req,
    );

    res.status(200).send(payload);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to fetch permissions" });
  }
});

/**
 * @openapi
 * /api/v1/permissions:
 *   post:
 *     summary: Create a new permission
 *     description: Create a new permission from the payload
 *     tags: [Permissions]
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
 *               description: Public permission for router.
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/Permission'
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
    const result = addPermissionSchema.safeParse(req.body);
    if (!result.success) {
      throw result.error;
    }
    const permission = await db
      .insert(permissions)
      .values(result.data)
      .returning();
    res.status(201).send(permission);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to create permission" });
  }
});

/**
 * @openapi
 * /api/v1/permissions/{permissionId}:
 *   get:
 *     summary: Get a permission
 *     description: Get a permission by ID
 *     tags: [Permissions]
 *     parameters:
 *       - in: path
 *         name: permissionId
 *         required: true
 *         schema:
 *           type: string
 *         description: Permission ID
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/Permission'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *
 */
router.get("/:permissionId", async (req: Request, res: Response) => {
  try {
    const permissionId = req.params.permissionId;
    const permission = getPermissionById(permissionId);
    if (!permission) {
      res.status(404).send({ message: "Unable to get permission" });
      return;
    }
    res.status(200).send(permission);
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to get permission" });
  }
});

/**
 * @openapi
 * /api/v1/permissions/{permissionId}:
 *   put:
 *     summary: Update a permission
 *     description: Update a permission
 *     tags: [Permissions]
 *     parameters:
 *       - in: path
 *         name: permissionId
 *         required: true
 *         schema:
 *           type: string
 *         description: Permission ID
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
 *               description: Public permission for router.
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/Permission'
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
router.put("/:permissionId", async (req: Request, res: Response) => {
  try {
    const permissionId = req.params.permissionId;
    const currentValue = await getPermissionById(permissionId);
    if (!currentValue) {
      res.status(404).send({ message: "Unable to get permission" });
      return;
    }

    const result = updatePermissionSchema.safeParse(req.body);
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
      throw new Error("No Changes to permission");
    }
    const payload: Record<string, number | string | Date | boolean> = {
      updatedAt: new Date(),
      // updatedBy: permissionId,
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
      .update(permissions)
      .set(payload)
      .where(eq(permissions.id, permissionId))
      .returning();
    res.status(200).send(updated);
    return;
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to update permission" });
  }
});

/**
 * @openapi
 * /api/v1/permissions/{permissionId}:
 *   delete:
 *     summary: Delete a permission
 *     description: Only admins can delete permissions.
 *     tags: [Permissions]
 *     security:
 *       - bearerAuth: []
 *     parameters:
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
router.delete("/:permissionId", async (req: Request, res: Response) => {
  try {
    const permissionId = req.params.permissionId;
    const rows = await db
      .delete(permissions)
      .where(eq(permissions.id, permissionId));
    res.status(200).send({ success: true, rows: rows.count });
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to delete permission" });
  }
});

async function getPermissionById(id: string) {
  return db.query.permissions.findFirst({
    where: eq(permissions.id, id),
  });
}

export default router;
