import {
  permissions,
  policies,
  rolePermissions,
  rolePolicies,
  roles,
  sessions,
  userRoles,
  users,
} from "@db/schema";
import { InferSelectModel, InferInsertModel } from "drizzle-orm";

export type Role = InferSelectModel<typeof roles>;
export type NewRole = InferInsertModel<typeof roles>;

export type Permission = InferSelectModel<typeof permissions>;
export type NewPermission = InferInsertModel<typeof permissions>;

export type RolePermission = InferSelectModel<typeof rolePermissions>;
export type NewRolePermission = InferInsertModel<typeof rolePermissions>;

export type Policy = InferSelectModel<typeof policies>;
export type NewPolicy = InferInsertModel<typeof policies>;

export type RolePolicy = InferSelectModel<typeof rolePolicies>;
export type NewRolePolicy = InferInsertModel<typeof rolePolicies>;

export type User = InferSelectModel<typeof users>;
export type NewUser = InferInsertModel<typeof users>;

export type UserRole = InferSelectModel<typeof userRoles>;
export type NewUserRole = InferInsertModel<typeof userRoles>;

export type Session = InferSelectModel<typeof sessions>;
export type NewSession = InferInsertModel<typeof sessions>;
