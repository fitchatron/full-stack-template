import request from "supertest";
import api from "@utils/config/api";
import { setMockUserFactory, publicUser, adminUser } from "@test/jest.setup";
import { db } from "@db/db";
import { and, count, eq } from "drizzle-orm";
import { policies } from "@db/schema";
import { faker } from "@faker-js/faker/.";

const SEED_VALUE = 1234;

describe("Policy DELETE API routes.", () => {
  describe("Delete a policy by ID.", () => {
    test("Authenticated user with the delete:policy policy and a valid policy ID. Responds with 200 status code and rows deleted", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const resource = "users";
      const action = "view";

      const intitalPolicy = await db.query.policies.findFirst({
        where: and(
          eq(policies.resource, resource),
          eq(policies.action, action),
        ),
      });

      expect(intitalPolicy).not.toBeUndefined();
      const policyId = intitalPolicy!.id;

      let countResult = await db.select({ count: count() }).from(policies);
      const intialPolicyCount = countResult.at(0)?.count ?? 0;

      const { status, body } = await request(api).delete(
        `/api/v1/polices/${policyId}`,
      );
      expect(status).toEqual(200);
      const rows: number = body.rows;
      expect(rows).toEqual(1);

      countResult = await db.select({ count: count() }).from(policies);
      const finalPolicyCount = countResult.at(0)?.count ?? 0;

      expect(finalPolicyCount).toEqual(finalPolicyCount - rows);

      const finalPolicy = await db.query.policies.findFirst({
        where: and(
          eq(policies.resource, resource),
          eq(policies.action, action),
        ),
      });

      expect(finalPolicy).toBeUndefined();
    });

    test("Authenticated user with the delete:policy policy and an invalid policy ID. Responds with 200 status code and no rows deleted", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const EXPECTED_ROWS_DELETED = 0;
      faker.seed(SEED_VALUE);
      const policyId = faker.string.uuid();
      const { status, body } = await request(api).delete(
        `/api/v1/policies/${policyId}`,
      );

      expect(status).toEqual(200);
      const rows: number = body.rows;
      expect(rows).toEqual(EXPECTED_ROWS_DELETED);
    });

    test("Authenticated user without the delete:policy policy and a valid policy ID. Responds with 403 status code", async () => {
      setMockUserFactory(() => ({
        user: publicUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const resource = "users";
      const action = "view";

      const policy = await db.query.policies.findFirst({
        where: and(
          eq(policies.resource, resource),
          eq(policies.action, action),
        ),
      });

      expect(policy).not.toBeUndefined();
      const policyId = policy!.id;

      const { status } = await request(api).delete(
        `/api/v1/polices/${policyId}`,
      );
      expect(status).toEqual(403);
    });

    test("Un-authenticated user and a valid policy ID. Responds with 401 status code", async () => {
      const resource = "users";
      const action = "view";

      const policy = await db.query.policies.findFirst({
        where: and(
          eq(policies.resource, resource),
          eq(policies.action, action),
        ),
      });

      expect(policy).not.toBeUndefined();
      const policyId = policy!.id;

      const { status } = await request(api).delete(
        `/api/v1/policies/${policyId}`,
      );
      expect(status).toEqual(401);
    });
  });
});
