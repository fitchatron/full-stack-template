import express, { Request, Response } from "express";
import { db } from "@db/db";
import { eventLogger } from "@utils/logger";
import { asc, eq } from "drizzle-orm";
import { roles } from "@db/schema";
import { withPagination } from "@db/utils";
import { addRoleSchema, updateRoleSchema } from "@validators/role";

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

app.post("/", async (req: Request, res: Response) => {
  try {
    const result = addRoleSchema.safeParse(req.body);
    if (!result.success) {
      throw result.error;
    }
    const role = await db.insert(roles).values(result.data).returning();
    res.status(201).send(role);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to create role" });
  }
});

app.get("/:roleId", async (req: Request, res: Response) => {
  try {
    const roleId = req.params.roleId;

    const role = await getRoleById(roleId);

    if (!role) {
      res.status(404).send({ message: "Unable to get role" });
      return;
    }
    res.status(200).send(role);
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
    const currentValue = await getRoleById(roleId);
    if (!currentValue) {
      res.status(404).send({ message: "Unable to get role" });
      return;
    }

    const result = updateRoleSchema.safeParse(req.body);
    if (!result.success) {
      throw result.error;
    }
    const newValue = result.data;
    const changes = new Set<string>();
    Object.entries(newValue).forEach(([key, value]) => {
      if (
        currentValue[
          key as keyof {
            name: string;
            description: string;
          }
        ] !== value
      ) {
        changes.add(key);
      }
    });

    if (changes.size === 0) {
      throw new Error("No Changes to role");
    }
    const payload: Record<string, number | string | Date | boolean> = {
      updatedAt: new Date(),
      // updatedBy: roleId,
    };
    changes.forEach((changeKey) => {
      payload[changeKey] =
        newValue[
          changeKey as keyof {
            name: string;
            description: string;
          }
        ] ?? "";
    });

    const updated = await db
      .update(roles)
      .set(payload)
      .where(eq(roles.id, roleId))
      .returning();
    res.status(200).send(updated);
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

async function getRoleById(id: string) {
  return db.query.roles.findFirst({
    where: eq(roles.id, id),
  });
}

export default app;
