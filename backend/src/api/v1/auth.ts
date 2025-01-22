import { Request, Response, Router } from "express";
// import { db } from "@db/db";
// import { userRoles } from "@db/schema";
// import { eventLogger } from "@utils/logger";
// import { and, eq } from "drizzle-orm";
// import { addUserRoleSchema } from "@validators/user-roles";
import { authService } from "@services/auth-service";

const router = Router();
const service = authService();

/**
 * @openapi
 * /api/v1/auth/register:
 *   post:
 *     summary: Create a new user
 *     description: Create a new user from the payload
 *     tags: [Auth]
 *     security: []
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
 *               - password
 *               - confirmPassword
 *             properties:
 *               firstName:
 *                 type: string
 *               lastName:
 *                 type: string
 *               email:
 *                 type: string
 *                 format: email
 *                 description: must be unique
 *               password:
 *                 type: string
 *               confirmPassword:
 *                 type: string
 *                 description: must match password
 *             example:
 *               firstName: John
 *               lastName: Doe
 *               email: john.doe@example.com
 *               password: s3cr3tPa55word
 *               confirmPassword: s3cr3tPa55word
 *     responses:
 *       201:
 *         description: OK
 *         headers:
 *           Set-Cookie:
 *             schema:
 *              type: string
 *              example: session=abcde12345; Path=/; HttpOnly
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
router.post("/register", async (req: Request, res: Response) => {
  const { data, error } = await service.signUpUser(req, res);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(201).json(data);
  return;
});

/**
 * @openapi
 * /api/v1/auth/login:
 *   post:
 *     summary: Sign in user
 *     description: Sign in an existing user
 *     tags: [Auth]
 *     security: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *                 description: must be unique
 *               password:
 *                 type: string
 *             example:
 *               email: john.doe@example.com
 *               password: s3cr3tPa55word
 *     responses:
 *       200:
 *         description: OK
 *         headers:
 *           Set-Cookie:
 *             schema:
 *              type: string
 *              example: session=abcde12345; Path=/; HttpOnly
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/User'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *
 */
router.post("/login", async (req: Request, res: Response) => {
  const { data, error } = await service.signInUser(req, res);

  if (error) {
    res.status(error.code).send(error.message);
    return;
  }
  res.status(201).json(data);
  return;
});

/**
 * @openapi
 * /api/v1/auth/reset-password:
 *   post:
 *     summary: Reset a password
 *     description: Reset a user's password
 *     tags: [Auth]
 *     security:
 *       cookieAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *               - confirmPassword
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *                 description: must be unique
 *               password:
 *                 type: string
 *               confirmPassword:
 *                 type: string
 *                 description: must match password
 *             example:
 *               email: john.doe@example.com
 *               password: s3cr3tPa55word
 *               confirmPassword: s3cr3tPa55word
 *     responses:
 *       200:
 *         description: OK
 *         content:
 *           application/json:
 *             schema:
 *              $ref: '#/components/schemas/User'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *
 */
router.post("/reset-password", async (req: Request, res: Response) => {
  res.status(405).json(true);
  return;
});

export default router;
