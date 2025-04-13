'use client';

import { useToast } from "@/lib/hooks/useToast";
import { useEffect, useState } from "react";

type ToastWithVisible = ReturnType<typeof useToast>["toasts"][0] & {
  visible: boolean;
};

export function CustomToaster() {
  const { toasts: originalToasts, dismiss } = useToast();
  const [toasts, setToasts] = useState<ToastWithVisible[]>([]);

  // Handle toast animations
  useEffect(() => {
    // Add new toasts with animation
    const newToasts = originalToasts.filter(
      (toast) => !toasts.some((t) => t.id === toast.id)
    );
    
    if (newToasts.length) {
      setToasts((prev) => [
        ...prev,
        ...newToasts.map((toast) => ({ ...toast, visible: true })),
      ]);
    }
    
    // Remove toasts that are no longer in the original list
    const currentToastIds = new Set(originalToasts.map((toast) => toast.id));
    setToasts((prev) =>
      prev.map((toast) => ({
        ...toast,
        visible: currentToastIds.has(toast.id),
      }))
    );
    
    // Eslint disable is needed because we only want to track originalToasts changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [originalToasts]);
  
  // Clean up toasts that are not visible after animation
  useEffect(() => {
    const toastsToRemove = toasts.filter(toast => !toast.visible);
    if (toastsToRemove.length === 0) return;
    
    const timeout = setTimeout(() => {
      setToasts((prev) => prev.filter((toast) => toast.visible));
    }, 300);
    
    return () => clearTimeout(timeout);
  }, [toasts]);

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col-reverse items-end gap-3 max-h-screen overflow-hidden pointer-events-none">
      {toasts.map(({ id, title, description, variant, visible }) => (
        <div
          key={id}
          className={`flex items-start w-full max-w-sm overflow-hidden rounded-lg shadow-xl pointer-events-auto transition-all duration-300 ${
            visible
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-4"
          } ${
            variant === "destructive"
              ? "bg-red-600 border border-red-400"
              : "bg-white border border-gray-200"
          }`}
        >
          <div className="flex-1 p-5">
            {title && (
              <h3 
                className={`text-sm font-semibold mb-0.5 ${
                  variant === "destructive" ? "text-white" : "text-gray-900"
                }`}
              >
                {title}
              </h3>
            )}
            {description && (
              <p 
                className={`text-sm ${
                  variant === "destructive" ? "text-white" : "text-gray-700"
                }`}
              >
                {description}
              </p>
            )}
          </div>
          <button
            onClick={() => dismiss(id)}
            className={`self-start p-2.5 transition-colors ${
              variant === "destructive"
                ? "text-white hover:text-red-100"
                : "text-gray-400 hover:text-gray-900"
            }`}
            aria-label="Close"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            <span className="sr-only">Close</span>
          </button>
        </div>
      ))}
    </div>
  );
} 