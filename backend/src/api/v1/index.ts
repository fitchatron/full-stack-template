import express from "express";
import auth from "@api/v1/auth";
import users from "@api/v1/users";
import roles from "@api/v1/roles";
import permissions from "@api/v1/permissions";
import status from "@api/v1/status";
import swaggerJsDoc from "swagger-jsdoc";
import swaggerUi from "swagger-ui-express";
import swaggerOptions from "@docs/swagger-options";

const VERSION = "v1";
const app = express();

// Set up Swagger UI
const swaggerDocs = swaggerJsDoc(swaggerOptions);

app.use(`/${VERSION}/api-docs`, swaggerUi.serve, swaggerUi.setup(swaggerDocs));
app.use(`/${VERSION}/auth`, auth);
app.use(`/${VERSION}/permissions`, permissions);
app.use(`/${VERSION}/roles`, roles);
app.use(`/${VERSION}/status`, status);
app.use(`/${VERSION}/users`, users);

export default app;
