describe("Policies POST API routes.", () => {
  describe("Create new Policy", () => {
    test("Authenticated user with the create policy policy, and a valid payload. Responds with 201 status code and created role", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the create policy policy and an invalid policy payload. Responds with 500 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the create policy policy and an existing policy payload. Responds with 400 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user without the create policy policy. Responds with 403 status code", async () => {
      expect(1).toEqual(2);
    });

    test("No User. Responds with 401 status code", async () => {
      expect(1).toEqual(2);
    });
  });
});
