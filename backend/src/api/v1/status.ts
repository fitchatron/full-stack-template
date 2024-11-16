import express, { Request, Response } from "express";

const app = express();

app.get("/", (req: Request, res: Response) => {
  res.status(200).send({
    status: "v1 running",
    runAt: new Date().toISOString(),
  });
  return;
});

export default app;
