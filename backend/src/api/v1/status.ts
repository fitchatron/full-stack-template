import { Request, Response, Router } from "express";

const router = Router();

/**
 * @openapi
 * /api/v1/status:
 *   get:
 *     summary: Check if server is running
 *     description: Get a response if servier is up.
 *     tags: [Status]
 *     responses:
 *       200:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              type: object
 *              properties:
 *                status:
 *                  type: string
 *                runAt:
 *                  type: string
 *                  format: date-time
 *             example:
 *               status: Running
 *               runAt: "2025-01-10T03:30:22.440Z"
 *
 */
router.get("/", (req: Request, res: Response) => {
  res.status(200).send({
    status: "Running",
    runAt: new Date().toISOString(),
  });
  return;
});

export default router;
