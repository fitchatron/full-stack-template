import { Request, Response, Router } from "express";
import { eventLogger } from "@utils/logger";
import { permissionService } from "@services/permission-service";

const router = Router();
const service = permissionService();

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
  const { data, error } = await service.getPermissions(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
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
  const { data, error } = await service.createPermission(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
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

    const { data, error } = await service.getPermissionById(permissionId);

    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
    return;
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
    const { data, error } = await service.updatePermissionById(
      permissionId,
      req.body,
    );
    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
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
    const { data, error } = await service.deletePermissionById(permissionId);
    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to delete permission" });
  }
});

export default router;
