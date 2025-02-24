import { NextFunction, Request, Response, Router } from "express";
import { eventLogger } from "@utils/logger";
import { roleService } from "@services/role-service";
import { rolePolicyService } from "@services/role-policy-service";
import permit from "@middleware/authorization";

const router = Router();
const service = roleService();
const { logEvent } = eventLogger();

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
router.get(
  "/",
  permit("roles", "view"),
  async (req: Request, res: Response, next: NextFunction) => {
    const { data, error } = await service.getRoles(req);

    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
    return;
  },
);

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
router.post(
  "/",
  permit("roles", "create"),
  async (req: Request, res: Response) => {
    const { data, error } = await service.createRole(req);

    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
    return;
  },
);

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
router.get(
  "/:roleId",
  permit("roles", "view"),
  async (req: Request, res: Response) => {
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
      logEvent({ type: "error", message: `${error}` });
      res.status(500).send({ message: "Unable to get role" });
    }
  },
);

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
router.put(
  "/:roleId",
  permit("roles", "edit"),
  async (req: Request, res: Response) => {
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
      logEvent({ type: "error", message: `${error}` });
      res.status(500).send({ message: "Unable to update role" });
    }
  },
);

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
router.delete(
  "/:roleId",
  permit("roles", "delete"),
  async (req: Request, res: Response) => {
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
      logEvent({ type: "error", message: `${error}` });
      res.status(500).send({ message: "Unable to delete role" });
    }
  },
);

/**
 *
 * @openapi
 * /api/v1/roles/{roleId}/policies:
 *   post:
 *     summary: Create a new role policy
 *     description: Create a new role policy for the given role
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
 *               - policyId
 *               - createdBy
 *               - modifiedBy
 *             properties:
 *               roleId:
 *                 type: string
 *               policyId:
 *                 type: string
 *               createdBy:
 *                 type: string
 *                 format: date-time
 *               modifiedBy:
 *                 type: string
 *                 format: date-time
 *             example:
 *               roleId: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *               policyId: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *               createdBy: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *               modifiedBy: 14c5f260-2ae0-49b7-9968-f6ed2e082526
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/RolePolicy'
 *       400:
 *         $ref: '#/components/responses/DuplicateEntity'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *
 */
router.post(
  "/:roleId/policies",
  permit("role_policies", "create"),
  async (req: Request, res: Response) => {
    const roleId = req.params.roleId;
    const { createRolePolicy } = rolePolicyService();

    const { data, error } = await createRolePolicy(roleId, req.body);
    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
    return;
  },
);

/**
 * @openapi
 * /api/v1/roles/{roleId}/policies/{policyId}:
 *   delete:
 *     summary: Delete a role policy
 *     description: Deletes a role policy given a role ID and policy ID
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
 *         name: policyId
 *         required: true
 *         schema:
 *           type: string
 *         description: Policy ID
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
  "/:roleId/policies/:policyId",
  permit("role_policies", "delete"),
  async (req: Request, res: Response) => {
    try {
      const roleId = req.params.roleId;
      const policyId = req.params.policyId;
      const { deleteRolePolicy } = rolePolicyService();

      const { data, error } = await deleteRolePolicy(roleId, policyId);
      if (error) {
        res.status(error.code).send(error.message);
        return;
      }
      res.status(200).send(data);
      return;
    } catch (error) {
      logEvent({ type: "error", message: `${error}` });
      res.status(500).send({ message: "Unable to delete role policy" });
    }
  },
);

export default router;
