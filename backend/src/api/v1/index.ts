import express from "express";
import users from "@api/v1/users";
import roles from "@api/v1/roles";
import permissions from "@api/v1/permissions";
import status from "@api/v1/status";

const VERSION = "v1";
const app = express();

app.use(`/${VERSION}/permissions`, permissions);
app.use(`/${VERSION}/roles`, roles);
app.use(`/${VERSION}/status`, status);
app.use(`/${VERSION}/users`, users);

export default app;
