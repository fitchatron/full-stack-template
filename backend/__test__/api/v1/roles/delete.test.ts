import request from "supertest";
import api from "@utils/config/api";
import { setMockUserFactory, publicUser, adminUser } from "@test/jest.setup";
import { Role } from "@models/orm-model";
import { PaginatedResponse } from "@models/pagination";
import { db } from "@db/db";
import { and, count, eq } from "drizzle-orm";
import { rolePolicies, roles } from "@db/schema";
import { faker } from "@faker-js/faker/.";

const SEED_VALUE = 1234;

describe("Roles DELETE API routes.", () => {
  describe("Delete a role by ID.", () => {
    test("Authenticated user with the delete roles policy and a valid role ID. Responds with 200 status code and rows deleted", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const roleName = "test-role-delete";

      const intitalRole = await db.query.roles.findFirst({
        where: eq(roles.name, roleName),
      });

      expect(intitalRole).not.toBeUndefined();
      const roleId = intitalRole!.id;

      let countResult = await db.select({ count: count() }).from(roles);
      const intialRoleCount = countResult.at(0)?.count ?? 0;

      const { status, body } = await request(api).delete(
        `/api/v1/roles/${roleId}`,
      );
      expect(status).toEqual(200);
      const rows: number = body.rows;
      expect(rows).toEqual(1);

      countResult = await db.select({ count: count() }).from(roles);
      const finalRoleCount = countResult.at(0)?.count ?? 0;

      expect(finalRoleCount).toEqual(intialRoleCount - rows);

      const finalRole = await db.query.roles.findFirst({
        where: eq(roles.name, roleName),
      });

      expect(finalRole).toBeUndefined();
    });

    test("Authenticated user with the delete roles policy and an invalid role ID. Responds with 200 status code and no rows deleted", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const EXPECTED_ROWS_DELETED = 0;
      faker.seed(SEED_VALUE);
      const roleId = faker.string.uuid();
      const { status, body } = await request(api).delete(
        `/api/v1/roles/${roleId}`,
      );

      expect(status).toEqual(200);
      const rows: number = body.rows;
      expect(rows).toEqual(EXPECTED_ROWS_DELETED);
    });

    test("Authenticated user without the delete roles policy and a valid role ID. Responds with 403 status code", async () => {
      setMockUserFactory(() => ({
        user: publicUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const roleName = "public";

      const role = await db.query.roles.findFirst({
        where: eq(roles.name, roleName),
      });

      expect(role).not.toBeUndefined();
      const roleId = role!.id;

      const { status } = await request(api).delete(`/api/v1/roles/${roleId}`);
      expect(status).toEqual(403);
    });

    test("Un-authenticated user and a valid role ID. Responds with 401 status code", async () => {
      const roleName = "public";

      const role = await db.query.roles.findFirst({
        where: eq(roles.name, roleName),
      });

      expect(role).not.toBeUndefined();
      const roleId = role!.id;

      const { status } = await request(api).delete(`/api/v1/roles/${roleId}`);
      expect(status).toEqual(401);
    });
  });

  describe("Delete a role policy by IDs", () => {
    test("Authenticated user with the delete role policy policy and a valid role ID. Responds with 200 status code and rows deleted", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const EXPECTED_ROWS_DELETED = 1;
      const firstRolePolicy = await db.query.rolePolicies.findFirst();

      expect(firstRolePolicy).not.toBeUndefined();

      let countResult = await db.select({ count: count() }).from(rolePolicies);
      const intialRolePolicyCount = countResult.at(0)?.count ?? 0;

      const { status, body } = await request(api).delete(
        `/api/v1/roles/${firstRolePolicy?.roleId}/policies/${firstRolePolicy?.policyId}`,
      );
      expect(status).toEqual(200);
      const rows: number = body.rows;
      expect(rows).toEqual(EXPECTED_ROWS_DELETED);

      countResult = await db.select({ count: count() }).from(rolePolicies);
      const finalRolePolicyCount = countResult.at(0)?.count ?? 0;

      expect(finalRolePolicyCount).toEqual(intialRolePolicyCount - rows);

      const finalRolePolicy = await db.query.rolePolicies.findFirst({
        where: and(
          eq(rolePolicies.roleId, firstRolePolicy!.roleId),
          eq(rolePolicies.policyId, firstRolePolicy!.policyId),
        ),
      });

      expect(finalRolePolicy).toBeUndefined();
    });

    test("Authenticated user with the delete role policy policy and an invalid role ID. Responds with 200 status code and no rows deleted", async () => {
      setMockUserFactory(() => ({
        user: adminUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const EXPECTED_ROWS_DELETED = 0;
      faker.seed(SEED_VALUE);
      const roleId = faker.string.uuid();
      const policyId = faker.string.uuid();

      const { status, body } = await request(api).delete(
        `/api/v1/roles/${roleId}/policies/${policyId}`,
      );
      expect(status).toEqual(200);
      const rows: number = body.rows;
      expect(rows).toEqual(EXPECTED_ROWS_DELETED);
    });

    test("Authenticated user without the delete role policy policy and a valid role ID. Responds with 403 status code", async () => {
      setMockUserFactory(() => ({
        user: publicUser,
        session: { id: "sessionId", token: "tokenId" },
      }));

      const firstRolePolicy = await db.query.rolePolicies.findFirst();

      expect(firstRolePolicy).not.toBeUndefined();

      let countResult = await db.select({ count: count() }).from(rolePolicies);
      const intialRolePolicyCount = countResult.at(0)?.count ?? 0;

      const { status, body } = await request(api).delete(
        `/api/v1/roles/${firstRolePolicy?.roleId}/policies/${firstRolePolicy?.policyId}`,
      );
      expect(status).toEqual(403);

      countResult = await db.select({ count: count() }).from(rolePolicies);
      const finalRolePolicyCount = countResult.at(0)?.count ?? 0;

      expect(finalRolePolicyCount).toEqual(intialRolePolicyCount);
    });

    test("Un-authenticated user and a valid role ID. Responds with 401 status code", async () => {
      const firstRolePolicy = await db.query.rolePolicies.findFirst();

      expect(firstRolePolicy).not.toBeUndefined();

      let countResult = await db.select({ count: count() }).from(rolePolicies);
      const intialRolePolicyCount = countResult.at(0)?.count ?? 0;

      const { status } = await request(api).delete(
        `/api/v1/roles/${firstRolePolicy?.roleId}/policies/${firstRolePolicy?.policyId}`,
      );
      expect(status).toEqual(401);

      countResult = await db.select({ count: count() }).from(rolePolicies);
      const finalRolePolicyCount = countResult.at(0)?.count ?? 0;

      expect(finalRolePolicyCount).toEqual(intialRolePolicyCount);
    });
  });
});
