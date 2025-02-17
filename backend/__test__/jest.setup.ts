import { closeConnection } from "@db/db";
import { Request, Response, NextFunction } from "express";

type RequestUser = {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
};

type RequestSession = {
  id: string;
  token: string;
};

const adminUser: RequestUser = {
  id: "2192b68f-8128-48a6-9a69-c268a489e5a3",
  email: "Haylee57@hotmail.com",
  firstName: "Chris",
  lastName: "Kemmer",
};

const userAdminUser: RequestUser = {
  id: "e680d30b-6131-48a8-8905-1661d29ee433",
  email: "Hans17@gmail.com",
  firstName: "Malika",
  lastName: "Murazik",
};
export const publicUser: RequestUser = {
  id: "7c8ea25d-5376-4964-966e-f91bad5091cc",
  email: "Norbert_Wunsch4@yahoo.com",
  firstName: "Tyree",
  lastName: "Weissnat",
};

// Default user factory
let mockUserSessionFactory: () => {
  user?: RequestUser;
  session?: RequestSession;
};

export const setMockUserFactory = (
  userSessionFactory: () => {
    user?: RequestUser;
    session?: RequestSession;
  },
) => {
  mockUserSessionFactory = userSessionFactory; // Set a new factory that generates users
};

export function resetMockUserFactory() {
  mockUserSessionFactory = () => ({ user: undefined, session: undefined });
}

jest.mock("../src/middleware/authentication", () => ({
  requireAuth: (req: Request, res: Response, next: NextFunction) => {
    const { user, session } = mockUserSessionFactory();

    if (!user) {
      res.status(401).json({ error: "Authentication required" });
      return;
    }
    if (!session) {
      res.status(401).json({ error: "Invalid session" });
      return;
    }

    if (session.token === "expired") {
      res.status(401).json({ error: "Invalid session" });
      return;
    }

    req.user = user;
    req.session = session;
    next();
  },
}));

beforeEach(() => {
  resetMockUserFactory();
});

afterEach(() => {
  resetMockUserFactory();
});

afterAll(async () => {
  closeConnection();
});
