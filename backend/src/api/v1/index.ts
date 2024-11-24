import express from "express";
import users from "@api/v1/users";
import roles from "@api/v1/roles";
import status from "@api/v1/status";

const VERSION = "v1";
const app = express();

app.use(`/${VERSION}/users`, users);
app.use(`/${VERSION}/roles`, roles);
app.use(`/${VERSION}/status`, status);

export default app;
