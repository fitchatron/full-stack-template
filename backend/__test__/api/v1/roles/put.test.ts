describe("Roles PUT API routes.", () => {
  describe("Update role by ID", () => {
    test("Authenticated user with the update roles policy, a valid role ID, and valid payload. Responds with 200 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the update roles policy, a valid role ID, and invalid payload. Responds with 500 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the update roles policy and an invalid role ID. Responds with 404 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user without the update roles policy. Responds with 403 status code", async () => {
      expect(1).toEqual(2);
    });

    test("No User. Responds with 401 status code", async () => {
      expect(1).toEqual(2);
    });
  });
});
