import { Request } from "express";
import { SQL } from "drizzle-orm";
import { PgColumn, PgSelect } from "drizzle-orm/pg-core";
import { db } from "@db/db";
import { PaginatedResponse } from "@models/pagination";

const START_PAGE = 1;

export async function withPagination<T extends PgSelect>(
  qb: T,
  orderByColumn: PgColumn | SQL | SQL.Aliased | undefined,
  page: number = 1,
  limit: number = 10,
  req: Request,
) {
  const total = await db.$count(qb);
  const pages = Math.ceil(total / limit);
  const startIndex = (page - 1) * limit;

  if (orderByColumn) qb.orderBy(orderByColumn);

  const result = await qb.limit(limit).offset(startIndex);

  const payload: PaginatedResponse<Awaited<T>> = {
    items: result,
    metadata: {
      limit,
      page,
      pages,
      total,
    },
    links: {
      first: `${req.headers.host}${req.baseUrl}?page=${START_PAGE}&limit=${limit}`,
      last: `${req.headers.host}${req.baseUrl}?page=${pages}&limit=${limit}`,
      prev: generatePreviousPageLink(req, page, pages, limit),
      next: generateNextPageLink(req, page, pages, limit),
    },
  };

  return payload;
}

function generatePreviousPageLink(
  req: Request,
  page: number,
  pages: number,
  limit: number,
): string | null {
  if (page <= START_PAGE || page === pages) return null;
  return `${req.headers.host}${req.baseUrl}?page=${page - 1}&limit=${limit}`;
}

function generateNextPageLink(
  req: Request,
  page: number,
  pages: number,
  limit: number,
): string | null {
  if (page === pages) return null;
  return `${req.headers.host}${req.baseUrl}?page=${page + 1}&limit=${limit}`;
}
