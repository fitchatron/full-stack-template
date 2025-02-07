import { db } from "@db/db";
import { permissions, rolePermissions, roles } from "@db/schema";
import {
  NewPermission,
  NewRole,
  NewRolePermission,
  Permission,
  Role,
} from "@models/orm-model";

export async function seedPermissions() {
  const newPermissions: NewPermission[] = [
    {
      name: "admin",
      description:
        "Admin permission for app. Users with this permission can perfirm any action",
    },
    {
      name: "public",
      description:
        "Public permission for app. Users with this permission can view public resources",
    },
    {
      name: "view:user",
      description: "Users with this permission can view users.",
    },
    {
      name: "create:user",
      description: "Users with this permission can create users.",
    },
    {
      name: "update:user",
      description: "Users with this permission can update users.",
    },
    {
      name: "delete:user",
      description: "Users with this permission can delete users.",
    },
    {
      name: "owner:user",
      description:
        "Users with this permission can manage users they are the owner of.",
    },
    {
      name: "view:role",
      description: "Users with this permission can view roles.",
    },
    {
      name: "create:role",
      description: "Users with this permission can create roles.",
    },
    {
      name: "update:role",
      description: "Users with this permission can update roles.",
    },
    {
      name: "delete:role",
      description: "Users with this permission can delete roles.",
    },
    {
      name: "view:permission",
      description: "Users with this permission can view permissions.",
    },
    {
      name: "create:permission",
      description: "Users with this permission can create permissions.",
    },
    {
      name: "update:permission",
      description: "Users with this permission can update permissions.",
    },
    {
      name: "delete:permission",
      description: "Users with this permission can delete permissions.",
    },
    {
      name: "view:role-permission",
      description: "Users with this role permission can view role permissions.",
    },
    {
      name: "create:role-permission",
      description:
        "Users with this role permission can create role permissions.",
    },
    {
      name: "update:role-permission",
      description:
        "Users with this role permission can update role permissions.",
    },
    {
      name: "delete:role-permission",
      description:
        "Users with this role permission can delete role permissions.",
    },
    {
      name: "view:user-role",
      description: "Users with this user role can view user roles.",
    },
    {
      name: "create:user-role",
      description: "Users with this user role can create user roles.",
    },
    {
      name: "update:user-role",
      description: "Users with this user role can update user roles.",
    },
    {
      name: "delete:user-role",
      description: "Users with this user role can delete user roles.",
    },
    {
      name: "view:session",
      description: "Users with this session can view sessions.",
    },
    {
      name: "create:session",
      description: "Users with this session can create sessions.",
    },
    {
      name: "update:session",
      description: "Users with this session can update sessions.",
    },
    {
      name: "delete:session",
      description: "Users with this session can delete sessions.",
    },
  ];

  const seededPermissions: Permission[] = await db
    .insert(permissions)
    .values(newPermissions)
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

  const publicPermisison = seededPermissions.find(
    (permission) => permission.name === "public",
  );
  const publicRole = seededRoles.find((role) => role.name === "public");

  const publicRolePermission: NewRolePermission[] = [
    { roleId: publicRole?.id ?? "", permissionId: publicPermisison?.id ?? "" },
  ];
  const userAdminPermisisons: Permission[] = seededPermissions.filter(
    (permission) =>
      [
        "view:user",
        "create:user",
        "update:user",
        "delete:user",
        "view:user-role",
        "create:user-role",
        "update:user-role",
        "delete:user-role",
      ].includes(permission.name),
  );
  const userAdminRole: Role | undefined = seededRoles.find(
    (role) => role.name === "user-admin",
  );

  const userAdminRolePermissions: NewRolePermission[] =
    userAdminPermisisons.map((permission) => {
      return {
        roleId: userAdminRole?.id ?? "",
        permissionId: permission.id ?? "",
      };
    });

  const adminRole: Role | undefined = seededRoles.find(
    (role) => role.name === "admin",
  );

  const adminRolePermisisons: NewRolePermission[] = seededPermissions.map(
    (permission) => {
      return {
        roleId: adminRole?.id ?? "",
        permissionId: permission.id ?? "",
      };
    },
  );

  const newRolePermissions: NewRolePermission[] = [
    ...publicRolePermission,
    ...userAdminRolePermissions,
    ...adminRolePermisisons,
  ];

  await db.insert(rolePermissions).values(newRolePermissions);
}
