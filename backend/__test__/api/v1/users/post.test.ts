describe("Users POST API routes.", () => {
  describe("Create new User", () => {
    test("Authenticated user with the create:user policy, and a valid payload. Responds with 201 status code and created role", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the create:user policy and an invalid role payload. Responds with 500 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the create:user policy and an existing role payload. Responds with 400 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user without the create:user policy. Responds with 403 status code", async () => {
      expect(1).toEqual(2);
    });

    test("No User. Responds with 401 status code", async () => {
      expect(1).toEqual(2);
    });
  });
});
