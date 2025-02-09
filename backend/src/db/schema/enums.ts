import { pgEnum } from "drizzle-orm/pg-core";

export const policyActionEnum = pgEnum("policyAction", [
  "view",
  "edit",
  "create",
  "delete",
]);

export const policyDecisionEnum = pgEnum("policyDecision", ["allow", "deny"]);
