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
  },
  apis: ["src/api/v1/*.ts"], // Path to the API docs in your routes
};

export default swaggerOptions;
