import React, { useState } from "react";
import { FiSend } from "react-icons/fi";

export default function InputBox({ onSendMessage, isLoading, disabled }) {
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading && !disabled) {
      onSendMessage(input);
      setInput("");
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="space-y-2" onSubmit={handleSubmit}>
      <div className="flex gap-3">
        <textarea
          className="flex-1 px-4 py-3 border border-gray-700 rounded-lg bg-gray-900 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-transparent resize-none"
          placeholder={
            disabled
              ? "Initialize pipeline first..."
              : "Ask a questions..."
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading || disabled}
          rows="1"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim() || disabled}
          title="Send message (Enter)"
          className="px-4 py-3 rounded bg-blue-600 text-white disabled:opacity-50 flex items-center justify-center"
        >
          <FiSend className="w-5 h-5" />
        </button>
      </div>
      {/* Helper text removed for a cleaner, minimal UI */}
    </form>
  );
}
