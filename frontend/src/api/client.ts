import axios from "axios";

export const apiClient = axios.create({
  baseURL: "/backend",
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  if (config.url) {
    config.url = config.url.replace(/\/+$/, "");
  }
  console.log("Request URL:", `${config.baseURL ?? ""}${config.url ?? ""}`);
  return config;
});
