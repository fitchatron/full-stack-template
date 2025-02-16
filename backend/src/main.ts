import api from "@utils/config/api";

const port = 8000;
// Start the server and listen on the specified port
api.listen(port, () => {
  // Log a message when the server is successfully running
  console.log(`Server is running on http://localhost:${port}`);
});
