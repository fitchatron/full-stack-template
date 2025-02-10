import { Router } from "express";
import { requireAuth } from "@middleware/authentication";
import auth from "@api/v1/auth";
import users from "@api/v1/users";
import roles from "@api/v1/roles";
import policies from "@api/v1/policies";
import status from "@api/v1/status";
import swaggerJsDoc from "swagger-jsdoc";
import swaggerUi from "swagger-ui-express";
import swaggerOptions from "@docs/swagger-options";

const VERSION = "v1";
const router = Router();

// Set up Swagger UI
const swaggerDocs = swaggerJsDoc(swaggerOptions);

router.use(
  `/${VERSION}/api-docs`,
  swaggerUi.serve,
  swaggerUi.setup(swaggerDocs, { swaggerOptions: { withCredentials: true } }),
);
router.use(`/${VERSION}/auth`, auth);
router.use(`/${VERSION}/policies`, requireAuth, policies);
router.use(`/${VERSION}/roles`, requireAuth, roles);
router.use(`/${VERSION}/status`, requireAuth, status);
router.use(`/${VERSION}/users`, requireAuth, users);

export default router;
