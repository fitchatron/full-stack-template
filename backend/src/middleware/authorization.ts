import { db } from "@db/db";
import { userRoles, roles, rolePolicies, policies } from "@db/schema";
import { and, eq, sql } from "drizzle-orm";
import { Request, Response, NextFunction } from "express";

// middleware for doing ABAC
export default function permit(
  resource: string,
  action: "view" | "create" | "edit" | "delete",
) {
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
          resource: policies.resource,
          action: policies.action,
          condition: policies.condition,
          decision: policies.decision,
        })
        .from(rolePolicies)
        .innerJoin(policies, eq(policies.id, rolePolicies.policyId))
        .innerJoin(roles, eq(roles.id, rolePolicies.roleId))
        .where(
          and(eq(policies.resource, resource), eq(policies.action, action)),
        )
        .as("sq");

      const currentUserPolicies = await db
        .select({
          userId: userRoles.userId,
          roleId: sq.roleId,
          roleName: sq.roleName,
          resource: sq.resource,
          action: sq.action,
          condition: sq.condition,
          decision: sq.decision,
        })
        .from(userRoles)
        .innerJoin(sq, eq(sq.roleId, userRoles.roleId))
        .where(and(eq(userRoles.userId, user.id)));

      if (!currentUserPolicies || currentUserPolicies.length === 0) {
        res.status(403).json({ error: "Forbidden" });
      }

      const decisions: ("allow" | "deny")[] = [];
      //TODO: check on conditions and decisions
      for (const row of currentUserPolicies) {
        // If there is no condition, just push the decision
        if (!row.condition) {
          decisions.push(row.decision);
          continue;
        }

        //TODO: check conditions
        decisions.push(row.decision);
        continue;
      }

      if (decisions.find((decision) => decision === "deny") !== undefined) {
        res.status(403).json({ error: "Forbidden" });
      }
      next();
    } catch (error) {
      console.error("Authorization middleware error:", error);
      res.status(500).json({ error: "Internal server error" });
    }
  };
}

// async function isOwner() {}
