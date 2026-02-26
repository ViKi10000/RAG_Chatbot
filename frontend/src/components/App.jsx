import React, { useEffect, useState } from "react";
import { chatbotAPI } from "../services/api";
import ChatWindow from "./ChatWindow";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [pipelineInfo, setPipelineInfo] = useState(null);
  const [isInitializing, setIsInitializing] = useState(false);
  const [backendError, setBackendError] = useState(null);
  const [initError, setInitError] = useState(null);

  
  useEffect(() => {
    const bootstrap = async () => {
      try {
        const healthRes = await chatbotAPI.health();

        if (healthRes.data.status !== "healthy") {
          setBackendError(
            "Backend is reachable but reported an unhealthy status.",
          );
          return;
        }

        setBackendError(null);

        // Check current status
        const statusRes = await chatbotAPI.status().catch(() => null);

        if (statusRes && statusRes.data.status === "ready") {
          setPipelineInfo(statusRes.data);
          setMessages([
            {
              id: Date.now(),
              type: "system",
              content: "You can ask questions now.",
            },
          ]);
          return;
        }

        // If not ready, try to initialize automatically once
        setIsInitializing(true);
        setInitError(null);

        await chatbotAPI.initialize();

        const afterInitStatus = await chatbotAPI.status().catch(() => null);

        if (afterInitStatus && afterInitStatus.data.status === "ready") {
          setPipelineInfo(afterInitStatus.data);
          setMessages([
            {
              id: Date.now(),
              type: "system",
              content: "You can ask questions now.",
            },
          ]);
        } else {
          setInitError("Pipeline did not report a ready status after init.");
        }
      } catch (err) {
       
        if (!pipelineInfo) {
          setBackendError(
            "Backend not available or initialization failed. Check that the API is running and VITE_API_URL is set correctly.",
          );
        }
      } finally {
        setIsInitializing(false);
      }
    };

    bootstrap();
  }, []);

  const appendMessage = (message) => {
    setMessages((prev) => [...prev, { id: Date.now(), ...message }]);
  };

  const handleSendMessage = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || !pipelineInfo || isLoadingChat) return;

    const userMessage = {
      type: "user",
      content: trimmed,
    };
    setMessages((prev) => [...prev, { id: Date.now(), ...userMessage }]);
    setIsLoadingChat(true);

    try {
      const res = await chatbotAPI.query(trimmed);
      const data = res.data;

      const botMessage = {
        type: "bot",
        content: data.answer,
        sources: data.sources || [],
        confidence: data.confidence ?? 0,
      };

      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, ...botMessage },
      ]);
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        "Failed to get response from the backend.";
      const errorMessage = {
        type: "error",
        content: `Error: ${detail}`,
      };
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 2, ...errorMessage },
      ]);
    } finally {
      setIsLoadingChat(false);
    }
  };

  const handleInitializePipeline = async () => {
    setIsInitializing(true);
    setInitError(null);
    try {
      await chatbotAPI.initialize();
      const statusRes = await chatbotAPI.status();

      if (statusRes.data.status === "ready") {
        setPipelineInfo(statusRes.data);
        appendMessage({
          type: "system",
          content: "You can ask questions now.",
        });
      } else {
        setInitError("Pipeline did not report a ready status after init.");
      }
    } catch (err) {
      setInitError(
        err.response?.data?.detail ||
          "Initialization failed. Check the backend logs.",
      );
    } finally {
      setIsInitializing(false);
    }
  };

  const handleClearHistory = async () => {
    setMessages([]);
    try {
      await chatbotAPI.clearHistory();
    } catch {
      // Non-critical; ignore errors
    }
  };

  const handleResetChat = () => {
    setMessages([]);
  };

  return (
    <div className="min-h-screen bg-dark-900 flex flex-col">
      {/* Simple header */}
      <header className="border-b border-gray-800 bg-gray-950">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-lg sm:text-xl font-semibold text-gray-50">
              Domain RAG Chatbot
            </h1>
            <p className="text-xs sm:text-sm text-gray-400">
              Ask questions about devcansol private limited.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {!pipelineInfo && (
              <>
                {isInitializing ? (
                  <span className="text-xs text-gray-300">
                    Initializing pipeline...
                  </span>
                ) : (
                  <button
                    onClick={handleInitializePipeline}
                    className="px-3 py-1 text-xs rounded bg-blue-600 text-white disabled:opacity-50"
                  >
                    Retry init
                  </button>
                )}
              </>
            )}
            <button
              onClick={handleResetChat}
              disabled={messages.length === 0}
              className="px-3 py-1 text-xs rounded border border-gray-700 text-gray-200 disabled:opacity-50"
            >
              Clear chat
            </button>
          </div>
        </div>
      </header>

      {backendError && (
        <div className="bg-red-950/60 border-b border-red-900">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 text-xs sm:text-sm text-red-100">
            {backendError}
          </div>
        </div>
      )}

      {initError && !pipelineInfo && (
        <div className="bg-amber-950/60 border-b border-amber-900">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 py-3 text-xs sm:text-sm text-amber-100">
            {initError}
          </div>
        </div>
      )}

      {/* Main chat area */}
      <main className="flex-1 flex">
        <div className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 py-4 sm:py-6">
          <ChatWindow
            messages={messages}
            isLoading={isLoadingChat}
            isReady={!!pipelineInfo}
            onSendMessage={handleSendMessage}
            onClearHistory={handleClearHistory}
          />
        </div>
      </main>
    </div>
  );
}
