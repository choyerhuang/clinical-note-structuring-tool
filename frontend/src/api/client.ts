import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/backend";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  if (config.url) {
    config.url = config.url.replace(/\/+$/, "");
  }
  return config;
});
