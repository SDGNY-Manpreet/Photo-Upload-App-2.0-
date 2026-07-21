import axios from "axios";

const api = axios.create({
  baseURL: "",
  timeout: 120000, // 2 minutes for large uploads
});

// ── Procore ──────────────────────────────────────────────────────────────────

export const fetchProcoreProjects = () =>
  api.get("/api/procore/projects").then((r) => r.data);

export const uploadToProcore = (formData, onProgress) =>
  api.post("/api/procore/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  }).then((r) => r.data);

// ── Shopify ───────────────────────────────────────────────────────────────────

export const fetchShopifyOrders = () =>
  api.get("/api/shopify/orders").then((r) => r.data);

export const uploadToShopify = (formData, onProgress) =>
  api.post("/api/shopify/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  }).then((r) => r.data);

// ── Special Projects ──────────────────────────────────────────────────────────

export const fetchSpecialProjects = () =>
  api.get("/api/special/projects").then((r) => r.data);

export const uploadToSpecial = (formData, onProgress) =>
  api.post("/api/special/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  }).then((r) => r.data);

// ── Health ────────────────────────────────────────────────────────────────────

export const fetchHealth = () =>
  api.get("/api/health").then((r) => r.data);
