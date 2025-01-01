import express, { Request, Response } from "express";
import { db } from "@db/db";
import { eventLogger } from "@utils/logger";
import { asc, eq } from "drizzle-orm";
import { withPagination } from "@db/utils";
import { permissions } from "@db/schema";
import {
  addPermissionSchema,
  updatePermissionSchema,
} from "@validators/permission";

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

app.post("/", async (req: Request, res: Response) => {
  try {
    const result = addPermissionSchema.safeParse(req.body);
    if (!result.success) {
      throw result.error;
    }
    const role = await db.insert(permissions).values(result.data).returning();
    res.status(201).send(role);
    return;
  } catch (error) {
    const { logEvent } = eventLogger({ type: "error", message: `${error}` });
    logEvent();
    res.status(500).send({ message: "Unable to create permission" });
  }
});

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
    const currentValue = await getPermissionById(permissionId);
    if (!currentValue) {
      res.status(404).send({ message: "Unable to get role" });
      return;
    }

    const result = updatePermissionSchema.safeParse(req.body);
    if (!result.success) {
      throw result.error;
    }
    const newValue = result.data;
    const changes = new Set<string>();
    Object.entries(newValue).forEach(([key, value]) => {
      currentValue[
        key as keyof {
          name: string;
          description: string;
        }
      ] !== value && changes.add(key);
    });

    if (changes.size === 0) {
      throw new Error("No Changes to role");
    }
    const payload: { [key: string]: any } = {
      updatedAt: new Date(),
      // updatedBy: permissionId,
    };
    changes.forEach((changeKey) => {
      payload[changeKey] =
        newValue[
          changeKey as keyof {
            name: string;
            description: string;
          }
        ];
    });

    const updated = await db
      .update(permissions)
      .set(payload)
      .where(eq(permissions.id, permissionId))
      .returning();
    res.status(200).send(updated);
    return;
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

async function getPermissionById(id: string) {
  return db.query.roles.findFirst({
    where: eq(permissions.id, id),
  });
}

export default app;
