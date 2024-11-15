import express, { Request, Response } from "express";
import cors from "cors";
import users from "./user";
import status from "./status";

const app = express();
app.use(cors());

// Define a route for the root path ('/')
app.get("/", (req: Request, res: Response) => {
	// Send a response to the client
	res.send("Hello, TypeScript + Node.js + Express!");
});
app.use("/users", users);
app.use("/status", status);

export default app;
