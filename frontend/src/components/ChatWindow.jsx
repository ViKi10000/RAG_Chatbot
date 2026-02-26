import React, { useRef, useEffect } from "react";
import Message from "./Message";
import InputBox from "./InputBox";
import { FiTrash2 } from "react-icons/fi";

export default function ChatWindow({
  messages,
  isLoading,
  isReady,
  onSendMessage,
  onClearHistory,
}) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="relative flex flex-col h-full flex-1 bg-dark-900/80 rounded-2xl border border-gray-800 shadow-lg overflow-hidden">
      {/* Chat Header */}
      <div className="bg-gray-950 border-b border-gray-800 px-4 sm:px-6 py-3 flex items-center justify-between">
        <span className="text-sm sm:text-base font-medium text-gray-100">
          Chat
        </span>
        {messages.length > 0 && (
          <button
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs sm:text-sm text-gray-300 hover:bg-gray-900 rounded-lg border border-gray-700 transition-colors"
            onClick={onClearHistory}
          >
            <FiTrash2 className="w-3 h-3 sm:w-4 sm:h-4" />
            Clear
          </button>
        )}
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto scrollbar-hide pb-24 sm:pb-28">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full px-4 sm:px-6 py-6 sm:py-8">
            <div className="text-center max-w-md space-y-2">
              <p className="text-sm text-gray-300">
                Ask a question about the documents to get started.
              </p>
              <p className="text-xs text-gray-500">
                Answers are generated strictly from the indexed content.
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="space-y-4 px-3 sm:px-6 py-4 sm:py-5">
              {messages.map((message) => (
                <Message key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex items-center gap-2 px-4 py-2 text-sm text-gray-400">
                  <span>Thinking…</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </>
        )}
      </div>


      <div className="fixed bottom-0 left-0 right-0 bg-gray-950 border-t border-gray-800 px-3 sm:px-6 py-3 sm:py-4">
        <div className="max-w-4xl mx-auto">
          <InputBox
            onSendMessage={onSendMessage}
            isLoading={isLoading}
            disabled={!isReady}
          />
        </div>
      </div>
    </div>
  );
}
