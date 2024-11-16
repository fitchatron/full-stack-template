export type PaginatedResponse<T> = {
  items: Array<T>;
  metadata: PaginatedMetadata;
};

type PaginatedMetadata = {
  limit: number;
  page: number;
  pages: number;
  total: number;
};
