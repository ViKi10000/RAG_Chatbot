import axios from "axios";

// API base URL and default models from env (see .env.example)
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const DEFAULT_EMBEDDING_MODEL = import.meta.env.VITE_EMBEDDING_MODEL || "all-MiniLM-L6-v2";
const DEFAULT_LLM_MODEL = import.meta.env.VITE_LLM_MODEL || "llama-3.1-8b-instant";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 503) {
      console.error("Pipeline not initialized. Please initialize first.");
    }
    return Promise.reject(error);
  },
);

export const chatbotAPI = {
  // Health check
  health: () => api.get("/health"),

  // Initialize pipeline (uses VITE_EMBEDDING_MODEL / VITE_LLM_MODEL if set)
  initialize: (modelName = DEFAULT_EMBEDDING_MODEL, llmModel = DEFAULT_LLM_MODEL) =>
    api.post("/init", {
      model_name: modelName,
      llm_model: llmModel,
    }),

  // Load documents
  loadDocuments: (dataDirectory) =>
    api.post("/load-documents", {
      data_directory: dataDirectory,
    }),

  // Query
  // Use a very low default minScore so we almost always
  // return some context; the backend will apply an extra
  // fallback if the threshold filters everything out.
  query: (question, topK = 5, minScore = 0.0) =>
    api.post("/query", {
      question,
      top_k: topK,
      min_score: minScore,
    }),

  // Get status
  status: () => api.get("/status"),

  // Get query history
  history: () => api.get("/history"),

  // Clear history
  clearHistory: () => api.post("/clear-history"),

  // Reset pipeline
  reset: () => api.delete("/reset"),
};

export default api;
