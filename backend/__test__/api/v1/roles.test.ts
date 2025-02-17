import request from "supertest";
import api from "@utils/config/api";
import { setMockUserFactory, publicUser } from "@test/jest.setup";

describe("Roles API routes. Authenticated user", () => {
  test("Authenticated public user. Responds with 200 status code", async () => {
    setMockUserFactory(() => ({
      user: publicUser,
      session: { id: "sessionId", token: "tokenId" },
    }));

    const response = await request(api).get("/api/v1/roles");
    expect(response.status).toEqual(200);
  });
});

describe("Roles API routes. Non-Authenticated user", () => {
  test("No User. Responds with 401 status code", async () => {
    const response = await request(api).get("/api/v1/roles");
    expect(response.status).toEqual(401);
  });
});
