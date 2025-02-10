import { db } from "@db/db";
import { resources } from "@db/schema";
import { NewResource } from "@models/orm-model";

export async function seedResources() {
  const newResources: NewResource[] = [
    {
      id: "policies",
      mappings: { owner: "created_by" },
    },
    {
      id: "resources",
      mappings: { owner: "created_by" },
    },
    {
      id: "role_policies",
      mappings: { owner: "created_by" },
    },
    {
      id: "roles",
      mappings: { owner: "created_by" },
    },
    {
      id: "sessions",
      mappings: { owner: "user_id" },
    },
    {
      id: "user_roles",
      mappings: { owner: "user_id" },
    },
    {
      id: "users",
      mappings: { owner: "id" },
    },
  ];

  await db.insert(resources).values(newResources);
}
