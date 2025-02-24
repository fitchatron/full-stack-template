import request from "supertest";
import api from "@utils/config/api";
import { setMockUserFactory, publicUser, adminUser } from "@test/jest.setup";
import { Role } from "@models/orm-model";
import { PaginatedResponse } from "@models/pagination";
import { db } from "@db/db";
import { count } from "drizzle-orm";
import { roles } from "@db/schema";

describe("Roles GET API routes.", () => {
  describe("Get all roles.", () => {
    test("Authenticated user with the read roles policy. Responds with 200 status code", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const { body, status } = await request(api).get("/api/v1/roles");
      expect(status).toEqual(200);

      const { links, items, metadata } = body as PaginatedResponse<Role[]>;

      const countResult = await db.select({ count: count() }).from(roles);
      const totalRoles = countResult.at(0)?.count ?? 0;
      expect(items.length).toEqual(totalRoles);
      expect(metadata.total).toEqual(totalRoles);
      expect(metadata.limit).toEqual(10);
      expect(metadata.page).toEqual(1);
      const expectedPages =
        totalRoles % metadata.limit === 0
          ? totalRoles / metadata.limit
          : parseInt(`${totalRoles / metadata.limit}`) + 1;
      expect(metadata.pages).toEqual(expectedPages);

      expect(links.first?.length).toBeGreaterThan(0);
      expect(links.last?.length).toBeGreaterThan(0);
      expect(links.next).toBeNull();
      expect(links.prev).toBeNull();
    });

    test("Authenticated user without the read roles policy. Responds with 403 status code", async () => {
      setMockUserFactory(() => ({
        user: publicUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const { status } = await request(api).get("/api/v1/roles");
      expect(status).toEqual(403);
    });

    test("No User. Responds with 401 status code", async () => {
      const { status } = await request(api).get("/api/v1/roles");
      expect(status).toEqual(401);
    });
  });

  describe("Get role by ID", () => {
    test("Authenticated user with the read roles policy and a valid Role ID. Responds with 200 status code", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const roleId = "b60c051d-f474-4af3-856a-2673e3d6bdf6";
      const { status, body } = await request(api).get(
        `/api/v1/roles/${roleId}`,
      );

      expect(status).toEqual(200);
      expect((body as Role).id).toEqual(roleId);
    });

    test("Authenticated user with the read roles policy and an invalid Role ID. Responds with 404 status code", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const roleId = "14c5f260-2ae0-49b7-9968-f6ed2e082526";
      const { status } = await request(api).get(`/api/v1/roles/${roleId}`);
      expect(status).toEqual(404);
    });

    test("Authenticated user without the read roles policy and a valid Role ID. Responds with 403 status code", async () => {
      setMockUserFactory(() => ({
        user: publicUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const roleId = "b60c051d-f474-4af3-856a-2673e3d6bdf6";
      const { status } = await request(api).get(`/api/v1/roles/${roleId}`);
      expect(status).toEqual(403);
    });

    test("No user and a valid Role ID. Responds with 401 status code", async () => {
      const roleId = "b60c051d-f474-4af3-856a-2673e3d6bdf6";
      const { status } = await request(api).get(`/api/v1/roles/${roleId}`);
      expect(status).toEqual(401);
    });
  });
});
