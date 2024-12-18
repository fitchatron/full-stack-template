import express, { Request, Response } from "express";
import { db } from "@db/db";
import { eventLogger } from "@utils/logger";
import { asc, eq } from "drizzle-orm";
import { withPagination } from "@db/utils";
import { permissions } from "@db/schema/permissions";

const app = express();

app.get("/", async (req: Request, res: Response) => {
  try {
    const page = parseInt(req.query.page?.toString() ?? "1");
    const limit = parseInt(req.query.limit?.toString() ?? "10");

    const query = db.select().from(permissions);

    const payload = await withPagination(
      query.$dynamic(),
      asc(permissions.id),
      page,
      limit,
      req,
    );

    res.status(200).send(payload);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to fetch permissions" });
  }
});

app.post("/", async (req: Request, res: Response) => {});

app.get("/:permissionId", async (req: Request, res: Response) => {
  try {
    const permissionId = req.params.permissionId;
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to get permission" });
  }
});

app.put("/:permissionId", async (req: Request, res: Response) => {
  try {
    const permissionId = req.params.permissionId;
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to update permission" });
  }
});

app.delete("/:permissionId", async (req: Request, res: Response) => {
  try {
    const permissionId = req.params.permissionId;
    const rows = await db
      .delete(permissions)
      .where(eq(permissions.id, permissionId));
    res.status(200).send({ success: true, rows: rows.count });
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to delete permission" });
  }
});

export default app;
