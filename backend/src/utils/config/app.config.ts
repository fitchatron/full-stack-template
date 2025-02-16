type AppConfig = {
  mode: "development" | "testing" | "production";
  hashValues: boolean;
  adminRoleName: string;
};

const DEV_CONFIG: AppConfig = {
  mode: "development",
  hashValues: false,
  adminRoleName: "superuser",
};

const PROD_CONFIG: AppConfig = {
  mode: "production",
  hashValues: true,
  adminRoleName: "superuser",
};

export const APP_CONFIG =
  (process.env.MODE ?? "development" === "development")
    ? DEV_CONFIG
    : PROD_CONFIG;
