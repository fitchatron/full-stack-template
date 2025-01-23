import { db } from "@db/db";
import { rolePermissions, userRoles, permissions, roles } from "@db/schema";
import { and, eq, sql } from "drizzle-orm";
import { Request, Response, NextFunction } from "express";

// middleware for doing role-based permissions
export default function permit(permissionName: string) {
  // return a middleware
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const user = req.user;

      if (!user) {
        res.status(401).json({ error: "Authentication required" });
        return;
      }

      const sq = db
        .select({
          roleId: roles.id,
          roleName: sql`${roles.name}`.as("roleName"),
          permissionName: sql`${permissions.name}`.as("permissionName"),
        })
        .from(rolePermissions)
        .innerJoin(
          permissions,
          eq(permissions.id, rolePermissions.permissionId),
        )
        .innerJoin(roles, eq(roles.id, rolePermissions.roleId))
        .as("sq");

      const currentUserRoles = await db
        .select({
          userId: userRoles.userId,
          roleId: sq.roleId,
          roleName: sq.roleName,
          permissionName: sq.permissionName,
        })
        .from(userRoles)
        .innerJoin(sq, eq(sq.roleId, userRoles.roleId))
        .where(
          and(
            eq(userRoles.userId, user.id),
            eq(sq.permissionName, permissionName),
          ),
        );

      if (!currentUserRoles || currentUserRoles.length === 0) {
        res.status(403).json({ error: "Unauthorized" });
      }
      next();
    } catch (error) {
      console.error("Authorization middleware error:", error);
      res.status(500).json({ error: "Internal server error" });
    }
  };
}
