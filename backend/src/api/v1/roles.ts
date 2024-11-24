import express, { Request, Response } from "express";
import { db } from "@db/db";
import { eventLogger } from "@utils/logger";
import { asc, eq } from "drizzle-orm";
import { roles } from "@db/schema/roles";
import { withPagination } from "@db/utils";

const app = express();

app.get("/", async (req: Request, res: Response) => {
  try {
    const page = parseInt(req.query.page?.toString() ?? "1");
    const limit = parseInt(req.query.limit?.toString() ?? "10");

    const query = db.select().from(roles);

    const payload = await withPagination(
      query.$dynamic(),
      asc(roles.id),
      page,
      limit,
      req,
    );

    res.status(200).send(payload);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to fetch roles" });
  }
});

app.post("/", async (req: Request, res: Response) => {});

app.get("/:roleId", async (req: Request, res: Response) => {
  try {
    const roleId = req.params.roleId;
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to get role" });
  }
});

app.put("/:roleId", async (req: Request, res: Response) => {
  try {
    const roleId = req.params.roleId;
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to update role" });
  }
});

app.delete("/:roleId", async (req: Request, res: Response) => {
  try {
    const roleId = req.params.roleId;
    const rows = await db.delete(roles).where(eq(roles.id, roleId));
    res.status(200).send({ success: true, rows: rows.count });
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to delete role" });
  }
});

export default app;
