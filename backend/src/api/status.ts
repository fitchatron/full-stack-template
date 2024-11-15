import express, { Request, Response } from "express";

const app = express();

app.get("/", (req: Request, res: Response) => {
  res.status(200).send({
    status: "running",
    runAt: new Date().toISOString(),
  });
});

export default app;
