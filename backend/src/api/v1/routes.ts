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

const router = Router();

// Set up Swagger UI
const swaggerDocs = swaggerJsDoc(swaggerOptions);

router.use(
  "/api-docs",
  swaggerUi.serve,
  swaggerUi.setup(swaggerDocs, { swaggerOptions: { withCredentials: true } }),
);
router.use("/auth", auth);
router.use("/policies", requireAuth, policies);
router.use("/roles", requireAuth, roles);
router.use("/status", status);
router.use("/users", requireAuth, users);

export default router;
