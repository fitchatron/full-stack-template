import express, { Request, Response } from "express";
import users from "@api/v1/user";
import status from "@api/v1/status";

const VERSION = "v1";
const app = express();

app.use(`/${VERSION}/users`, users);
app.use(`/${VERSION}/status`, status);

export default app;
