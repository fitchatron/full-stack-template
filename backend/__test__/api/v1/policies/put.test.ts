describe("Policies PUT API routes.", () => {
  describe("Update policy by ID", () => {
    test("Authenticated user with the update policies policy, a valid policy ID, and valid payload. Responds with 200 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the update policies policy, a valid policy ID, and invalid payload. Responds with 500 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the update policies policy and an invalid policy ID. Responds with 404 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user without the update policies policy. Responds with 403 status code", async () => {
      expect(1).toEqual(2);
    });

    test("No User. Responds with 401 status code", async () => {
      expect(1).toEqual(2);
    });
  });
});
