/* eslint-disable @typescript-eslint/consistent-type-definitions */
declare global {
  namespace Express {
    interface Request {
      user?: {
        id: string;
        email: string;
        firstName: string;
        lastName: string;
      };
      session?: {
        id: string;
        token: string;
      };
    }
    interface Response {
      cookie?: {
        httpOnly: boolean;
        secure: boolean;
        sameSite: "lax";
        expires: Date;
      };
    }
  }
}

export {};
