import { db } from "@db/db";
import { policies, rolePolicies, roles } from "@db/schema";
import {
  NewPolicy,
  NewRole,
  NewRolePolicy,
  Policy,
  Role,
} from "@models/orm-model";

export async function seedPolicies() {
  const newPolicies: NewPolicy[] = [
    {
      resource: "users",
      action: "view",
      condition: { self: true },
      decision: "allow",
    },
    {
      resource: "users",
      action: "view",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "users",
      action: "create",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "users",
      action: "edit",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "users",
      action: "delete",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "users",
      action: "delete",
      condition: { self: true },
      decision: "deny",
    },
    {
      resource: "roles",
      action: "view",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "roles",
      action: "create",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "roles",
      action: "edit",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "roles",
      action: "delete",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "policies",
      action: "view",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "policies",
      action: "create",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "policies",
      action: "edit",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "policies",
      action: "delete",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "role_policies",
      action: "view",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "role_policies",
      action: "create",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "role_policies",
      action: "edit",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "role_policies",
      action: "delete",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "sessions",
      action: "view",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "sessions",
      action: "view",
      condition: { self: true },
      decision: "allow",
    },
    {
      resource: "sessions",
      action: "create",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "sessions",
      action: "create",
      condition: { self: true },
      decision: "allow",
    },
    {
      resource: "sessions",
      action: "edit",
      condition: { self: true },
      decision: "allow",
    },
    {
      resource: "sessions",
      action: "delete",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "sessions",
      action: "delete",
      condition: { self: true },
      decision: "allow",
    },
    {
      resource: "user_roles",
      action: "view",
      condition: { self: true },
      decision: "allow",
    },
    {
      resource: "user_roles",
      action: "view",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "user_roles",
      action: "create",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "user_roles",
      action: "edit",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "user_roles",
      action: "delete",
      condition: undefined,
      decision: "allow",
    },
    {
      resource: "user_roles",
      action: "view",
      condition: { self: true },
      decision: "allow",
    },
    {
      resource: "user_roles",
      action: "create",
      condition: { self: true },
      decision: "allow",
    },
    {
      resource: "user_roles",
      action: "edit",
      condition: { self: true },
      decision: "allow",
    },
    {
      resource: "user_roles",
      action: "delete",
      condition: { self: true },
      decision: "allow",
    },
  ];

  const seededPolicies: Policy[] = await db
    .insert(policies)
    .values(newPolicies)
    .returning();

  const newRoles: NewRole[] = [
    {
      name: "admin",
      description: "Admin role for app.",
    },
    {
      name: "public",
      description: "Public role for app.",
    },
    {
      name: "user-admin",
      description:
        "User Admin role for app. Role is responsible for managing users",
    },
  ];

  const seededRoles: Role[] = await db
    .insert(roles)
    .values(newRoles)
    .returning();

  const publicPolicies = seededPolicies.filter(
    (policy) =>
      (policy.condition as Record<string, string | number | object | boolean>)
        ?.self ||
      (policy.resource === "policies" && policy.action === "view") ||
      (policy.resource === "roles" && policy.action === "view") ||
      (policy.resource === "role_policies" && policy.action === "view"),
  );
  const publicRole = seededRoles.find((role) => role.name === "public");

  const publicRolePolices: NewRolePolicy[] = publicPolicies.map((policy) => {
    return { policyId: policy.id ?? "", roleId: publicRole?.id ?? "" };
  });

  const userAdminPolicies: Policy[] = seededPolicies.filter(
    (policy) =>
      (policy.resource === "users" && !policy.condition) ||
      policy.resource === "user_roles",
  );
  const userAdminRole: Role | undefined = seededRoles.find(
    (role) => role.name === "user-admin",
  );

  const userAdminRolePolicies: NewRolePolicy[] = userAdminPolicies.map(
    (policy) => {
      return {
        roleId: userAdminRole?.id ?? "",
        policyId: policy.id ?? "",
      };
    },
  );

  const adminRole: Role | undefined = seededRoles.find(
    (role) => role.name === "admin",
  );

  const adminRolePolicies: NewRolePolicy[] = seededPolicies.map((policy) => {
    return {
      roleId: adminRole?.id ?? "",
      policyId: policy.id ?? "",
    };
  });

  const newRolePolicies: NewRolePolicy[] = [
    ...publicRolePolices,
    ...userAdminRolePolicies,
    ...adminRolePolicies,
  ];

  await db.insert(rolePolicies).values(newRolePolicies);
}
