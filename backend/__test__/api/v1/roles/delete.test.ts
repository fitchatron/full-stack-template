import request from "supertest";
import api from "@utils/config/api";
import { setMockUserFactory, publicUser, adminUser } from "@test/jest.setup";
import { Role } from "@models/orm-model";
import { PaginatedResponse } from "@models/pagination";
import { db } from "@db/db";
import { count } from "drizzle-orm";
import { roles } from "@db/schema";

describe("Roles DELETE API routes.", () => {
  describe("Delete a role by ID.", () => {
    test("Authenticated user with the delete roles policy and a valid role ID. Responds with 200 status code and rows deleted", async () => {});

    test("Authenticated user with the delete roles policy and an invalid role ID. Responds with 404 status code", async () => {});
  });

  describe("Delete a role policy by IDs", () => {});
});
