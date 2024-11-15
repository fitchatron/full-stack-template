import express, { Request, Response } from "express";

const app = express();

app.get("/", (req: Request, res: Response) => {
  res.send("User list");
});

app.post("/", (req: Request, res: Response) => {
  res.send("Create new user");
});

app.get("/:userId", (req: Request, res: Response) => {
  const userId = req.params.userId;
  res.send(`Get user by Id ${userId}`);
});

app.put("/:userId", (req: Request, res: Response) => {
  const userId = req.params.userId;
  res.send(`Update user by Id ${userId}`);
});

app.delete("/:userId", (req: Request, res: Response) => {
  const userId = req.params.userId;
  res.send(`Delete user by Id ${userId}`);
});

export default app;
