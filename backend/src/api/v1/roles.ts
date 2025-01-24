import { Request, Response, Router } from "express";
import { eventLogger } from "@utils/logger";
import { roleService } from "@services/role-service";
import { rolePermissionService } from "@services/role-permission-service";

const router = Router();
const service = roleService();

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
  const { data, error } = await service.getRoles(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
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
  const { data, error } = await service.createRole(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
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

    const { data, error } = await service.getRoleById(roleId);

    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
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
    const { data, error } = await service.updateRoleById(roleId, req.body);
    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
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
    const { data, error } = await service.deleteRoleById(roleId);
    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
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
  const roleId = req.params.roleId;
  const { createRolePermission } = rolePermissionService();

  const { data, error } = await createRolePermission(roleId, req.body);
  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
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
      const { deleteRolePermission } = rolePermissionService();

      const { data, error } = await deleteRolePermission(roleId, permissionId);
      if (error) {
        res.status(error.code).send(error.message);
        return;
      }
      res.status(200).send(data);
      return;
    } catch (error) {
      const { logEvent } = eventLogger({ type: "error", message: `${error}` });
      logEvent();
      res.status(500).send({ message: "Unable to delete role permission" });
    }
  },
);

export default router;
