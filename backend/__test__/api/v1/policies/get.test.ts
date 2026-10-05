import request from "supertest";
import api from "@utils/config/api";
import { setMockUserFactory, publicUser, adminUser } from "@test/jest.setup";
import { Policy } from "@models/orm-model";
import { PaginatedResponse } from "@models/pagination";
import { db } from "@db/db";
import { and, count, eq } from "drizzle-orm";
import { policies } from "@db/schema";

describe("Policies GET API routes.", () => {
  describe("Get all policies", () => {
    test("Authenticated user with the view:policy policy. Responds with 200 status code", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const { body, status } = await request(api).get("/api/v1/policies");
      expect(status).toEqual(200);

      const { links, items, metadata } = body as PaginatedResponse<Policy[]>;

      const countResult = await db.select({ count: count() }).from(policies);
      const totalPolicies = countResult.at(0)?.count ?? 0;
      expect(items.length).toEqual(totalPolicies);
      expect(metadata.total).toEqual(totalPolicies);
      expect(metadata.limit).toEqual(10);
      expect(metadata.page).toEqual(1);
      const expectedPages =
        totalPolicies % metadata.limit === 0
          ? totalPolicies / metadata.limit
          : parseInt(`${totalPolicies / metadata.limit}`) + 1;
      expect(metadata.pages).toEqual(expectedPages);

      expect(links.first?.length).toBeGreaterThan(0);
      expect(links.last?.length).toBeGreaterThan(0);
      expect(links.next).toBeNull();
      expect(links.prev).toBeNull();
    });

    test("Authenticated user without the view:policy policy. Responds with 403 status code", async () => {
      setMockUserFactory(() => ({
        user: publicUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const { status } = await request(api).get("/api/v1/policies");
      expect(status).toEqual(403);
    });

    test("No User. Responds with 401 status code", async () => {
      const { status } = await request(api).get("/api/v1/policies");
      expect(status).toEqual(401);
    });
  });

  describe("Get role by ID", () => {
    test("Authenticated user with the view:policy policy and a valid Policy ID. Responds with 200 status code", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const resource = "users";
      const action = "view";
      const queryPolicy = await db.query.policies.findFirst({
        where: and(
          eq(policies.resource, resource),
          eq(policies.action, action),
        ),
      });

      expect(queryPolicy).not.toBeUndefined();
      const policyId = queryPolicy!.id;

      const { status, body } = await request(api).get(
        `/api/v1/policies/${policyId}`,
      );

      expect(status).toEqual(200);
      expect((body as Policy).id).toEqual(policyId);
    });

    test("Authenticated user with the view:policy policy and an invalid Policy ID. Responds with 404 status code", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const policyId = "14c5f260-2ae0-49b7-9968-f6ed2e082526";
      const { status } = await request(api).get(`/api/v1/policies/${policyId}`);
      expect(status).toEqual(404);
    });

    test("Authenticated user without the view:policy policy and a valid Policy ID. Responds with 403 status code", async () => {
      setMockUserFactory(() => ({
        user: publicUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const resource = "users";
      const action = "view";
      const queryPolicy = await db.query.policies.findFirst({
        where: and(
          eq(policies.resource, resource),
          eq(policies.action, action),
        ),
      });

      expect(queryPolicy).not.toBeUndefined();
      const policyId = queryPolicy!.id;
      const { status } = await request(api).get(`/api/v1/policies/${policyId}`);
      expect(status).toEqual(403);
    });

    test("No user and a valid Policy ID. Responds with 401 status code", async () => {
      const resource = "users";
      const action = "view";
      const queryPolicy = await db.query.policies.findFirst({
        where: and(
          eq(policies.resource, resource),
          eq(policies.action, action),
        ),
      });

      expect(queryPolicy).not.toBeUndefined();
      const policyId = queryPolicy!.id;
      const { status } = await request(api).get(`/api/v1/policies/${policyId}`);
      expect(status).toEqual(401);
    });
  });
});
