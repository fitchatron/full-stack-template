import { Request, Response, NextFunction } from "express";

type SessionUser = {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
};

const publicUser: SessionUser = {
  id: "some-uuid",
  email: "john.doe@example.com",
  firstName: "John",
  lastName: "Doe",
};

let mockUserFactory: () => SessionUser | undefined = () => undefined; // Default user factory

export const setMockUserFactory = (
  userFactory: () => SessionUser | undefined,
) => {
  mockUserFactory = userFactory; // Set a new factory that generates users
};

jest.mock("../src/middleware/authentication", () => ({
  requireAuth: (req: Request, res: Response, next: NextFunction) => {
    req.user = mockUserFactory();
    next();
  },
}));
