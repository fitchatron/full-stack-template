import { Request, Response, Router } from "express";
import { eventLogger } from "@utils/logger";
import { policyService } from "@services/policy-service";

const router = Router();
const service = policyService();
const { logEvent } = eventLogger();

/**
 * @openapi
 * /api/v1/policies:
 *   get:
 *     summary: Retrieve list of policies
 *     description: Get a paginated list of policies.
 *     tags: [Policies]
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
 *                    $ref: '#/components/schemas/Policy'
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
  const { data, error } = await service.getPolicies(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
});

/**
 * @openapi
 * /api/v1/policies:
 *   post:
 *     summary: Create a new policy
 *     description: Create a new policy from the payload
 *     tags: [Policies]
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
 *               description: Public policy for router.
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/Policy'
 *       400:
 *         $ref: '#/components/responses/DuplicateEntity'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *
 */
router.post("/", async (req: Request, res: Response) => {
  const { data, error } = await service.createPolicy(req);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(200).send(data);
  return;
});

/**
 * @openapi
 * /api/v1/policies/{policyId}:
 *   get:
 *     summary: Get a policy
 *     description: Get a policy by ID
 *     tags: [Policies]
 *     parameters:
 *       - in: path
 *         name: policyId
 *         required: true
 *         schema:
 *           type: string
 *         description: policy ID
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/Policy'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       403:
 *         $ref: '#/components/responses/Forbidden'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *
 */
router.get("/:policyId", async (req: Request, res: Response) => {
  try {
    const policyId = req.params.policyId;

    const { data, error } = await service.getPolicyById(policyId);

    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
    return;
  } catch (error) {
    logEvent({ type: "error", message: `${error}` });
    res.status(500).send({ message: "Unable to get policy" });
  }
});

/**
 * @openapi
 * /api/v1/policies/{policyId}:
 *   put:
 *     summary: Update a policy
 *     description: Update a policy
 *     tags: [Policies]
 *     parameters:
 *       - in: path
 *         name: policyId
 *         required: true
 *         schema:
 *           type: string
 *         description: policy ID
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
 *               description: Public policy for router.
 *     responses:
 *       201:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/Policy'
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
router.put("/:policyId", async (req: Request, res: Response) => {
  try {
    const policyId = req.params.policyId;
    const { data, error } = await service.updatePolicyById(policyId, req.body);
    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
    return;
  } catch (error) {
    logEvent({ type: "error", message: `${error}` });
    res.status(500).send({ message: "Unable to update policy" });
  }
});

/**
 * @openapi
 * /api/v1/policies/{policyId}:
 *   delete:
 *     summary: Delete a policy
 *     description: Only admins can delete policies.
 *     tags: [Policies]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: policyId
 *         required: true
 *         schema:
 *           type: string
 *         description: policy ID
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
router.delete("/:policyId", async (req: Request, res: Response) => {
  try {
    const policyId = req.params.policyId;
    const { data, error } = await service.deletePolicyById(policyId);
    if (error) {
      res.status(error.code).send(error.message);
      return;
    }
    res.status(200).send(data);
    return;
  } catch (error) {
    logEvent({ type: "error", message: `${error}` });
    res.status(500).send({ message: "Unable to delete policy" });
  }
});

export default router;
