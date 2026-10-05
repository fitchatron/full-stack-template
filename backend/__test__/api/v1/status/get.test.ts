import request from "supertest";
import api from "@utils/config/api";

describe("Status", () => {
  test("Responds with 200 status code", async () => {
    const response = await request(api).get("/api/v1/status");

    expect(response.status).toEqual(200);
    expect(response.headers["content-type"]).toMatch(/json/);
    expect(response.body.status).toMatch(/Running/i);
  });
});
