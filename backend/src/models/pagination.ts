export type PaginatedResponse<T> = {
  items: T;
  metadata: PaginatedMetadata;
  links: Link;
};

type Link = {
  first: string | null;
  last: string | null;
  prev: string | null;
  next: string | null;
};

type PaginatedMetadata = {
  limit: number;
  page: number;
  pages: number;
  total: number;
};
