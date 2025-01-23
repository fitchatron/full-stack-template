type AppConfig = {
  mode: "development" | "testing" | "production";
  hashValues: boolean;
};
const DEV_CONFIG: AppConfig = {
  mode: "development",
  hashValues: false,
};

const PROD_CONFIG: AppConfig = {
  mode: "production",
  hashValues: true,
};

export const APP_CONFIG =
  (process.env.MODE ?? "development" === "development")
    ? DEV_CONFIG
    : PROD_CONFIG;
