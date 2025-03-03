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

export const adminUser: RequestUser = {
  id: "f8fbb3f0-46c3-4df2-a906-0f6fcd2192b6",
  email: "Karli.Nienow@gmail.com",
  firstName: "Tressie",
  lastName: "Brekke",
};

const userAdminUser: RequestUser = {
  id: "aa09a4a3-89d0-4560-9d26-36936fceb222",
  email: "Chase30@gmail.com",
  firstName: "Shanon",
  lastName: "Herman",
};

export const publicUser: RequestUser = {
  id: "9c268a48-9e5a-4372-be6d-6e659dd9193b",
  email: "Braxton_Hickle4@yahoo.com",
  firstName: "Jordi",
  lastName: "Bergnaum",
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
      console.log("Mock auth: No user, sending 401");

      if (!res.headersSent) {
        res.status(401).json({ error: "Authentication required" });
      }
      return;
    }
    if (!session) {
      console.log("Mock auth: Invalid session, sending 401");
      if (!res.headersSent) {
        res.status(401).json({ error: "Invalid session" });
      }
      return;
    }

    if (session.token === "expired") {
      console.log("Mock auth: Session Expired, sending 401");
      if (!res.headersSent) {
        res.status(401).json({ error: "Invalid session" });
      }
      return;
    }

    console.log("Mock auth: Setting user");
    if (!res.headersSent) {
      req.user = user;
      req.session = session;
      next();
    }
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
