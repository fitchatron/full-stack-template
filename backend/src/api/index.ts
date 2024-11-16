import express, { Request, Response } from "express";
import cors from "cors";
import v1 from "@api/v1/index";

const app = express();
app.use(express.json());
app.use(express.urlencoded());
app.use(cors());

// Define a route for the root path ('/')
app.get("/", (req: Request, res: Response) => {
  // Send a response to the client
  res.send("Hello, TypeScript + Node.js + Express!");
  return;
});
app.use(`/api`, v1);

export default app;
