import request from "supertest";
import api from "@utils/config/api";
import { setMockUserFactory } from "../../jest.setup";

describe("Roles API routes", () => {
  test("Authenticated user. Responds with 200 status code", async () => {
    setMockUserFactory(() => ({
      id: "some-uuid",
      email: "john.doe@example.com",
      firstName: "John",
      lastName: "Doe",
    }));

    const response = await request(api).get("/api/v1/roles");
    console.log("the resp is", response);

    expect(response.status).toEqual(200);
  });
  test("No User. Responds with 401 status code", async () => {
    const response = await request(api).get("/api/v1/roles");
    console.log("the resp is", response);

    expect(response.status).toEqual(401);
  });
});
