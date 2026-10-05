describe("Roles POST API routes.", () => {
  describe("Create new Role", () => {
    test("Authenticated user with the create roles policy, and a valid payload. Responds with 201 status code and created role", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the create roles policy and an invalid role payload. Responds with 500 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the create roles policy and an existing role payload. Responds with 400 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user without the create roles policy. Responds with 403 status code", async () => {
      expect(1).toEqual(2);
    });

    test("No User. Responds with 401 status code", async () => {
      expect(1).toEqual(2);
    });
  });

  describe("Create new Role Policy", () => {
    test("Authenticated user with the create role polices policy, and a valid role policy payload. Responds with 201 status code and created role", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the create role polices policy and an invalid role policy payload. Responds with 500 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user with the create role polices policy and an existing role policy payload. Responds with 400 status code", async () => {
      expect(1).toEqual(2);
    });

    test("Authenticated user without the create role polices policy. Responds with 403 status code", async () => {
      expect(1).toEqual(2);
    });

    test("No User. Responds with 401 status code", async () => {
      expect(1).toEqual(2);
    });
  });
});
