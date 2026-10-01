// Proxy /api/* to the FastAPI backend so the browser never deals with CORS.
export default { async rewrites() { return [{ source: "/api/:p*", destination: "http://localhost:8000/api/:p*" }]; } };
