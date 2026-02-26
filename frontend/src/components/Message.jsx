import React from "react";
import { FiAlertCircle } from "react-icons/fi";

export default function Message({ message }) {

  if (message.type === "system") {
    return (
      <div className="animate-fadeIn">
        <div className="px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-sm text-gray-100">
          ℹ️ {message.content}
        </div>
      </div>
    );
  }

  if (message.type === "error") {
    return (
      <div className="animate-fadeIn">
        <div className="flex gap-3 p-4 bg-red-950/60 border border-red-900 rounded-lg">
          <FiAlertCircle className="w-5 h-5 text-red-300 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-100">{message.content}</div>
        </div>
      </div>
    );
  }

  if (message.type === "user") {
    return (
      <div className="animate-fadeIn flex justify-end">
        <div className="max-w-xs lg:max-w-md px-4 py-3 bg-primary-600 text-white rounded-lg rounded-br-none shadow-md">
          <p className="text-sm">{message.content}</p>
        </div>
      </div>
    );
  }

  if (message.type === "bot") {
    return (
      <div className="animate-fadeIn flex justify-start">
        <div className="max-w-xs lg:max-w-md">
          <div className="px-4 py-3 bg-gray-900 border border-gray-800 rounded-lg rounded-bl-none shadow-md space-y-2">
            <p className="text-sm text-gray-100 whitespace-pre-line">
              {message.content}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return null;
}
