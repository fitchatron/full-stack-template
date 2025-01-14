import { Options } from "swagger-jsdoc";

const swaggerOptions: Options = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "Express API Documentation",
      version: "1.0.0",
      description: "API documentation for your Express app",
    },
    servers: [
      {
        url: "http://localhost:8000",
      },
    ],
    tags: [
      {
        name: "Permissions",
        description: "Permission management and retrieval",
      },
      { name: "Roles", description: "Role management and retrieval" },
      { name: "Status", description: "Server status" },
      { name: "Users", description: "User management and retrieval" },
    ],
  },
  apis: ["src/docs/*.yml", "src/api/v1/*.ts"], // Path to the API docs in your routes
};

export default swaggerOptions;
