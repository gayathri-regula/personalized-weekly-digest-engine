import React, { useState } from "react";
import { generateDigest } from "../api/client";
import { Digest } from "../types";

interface GenerateButtonProps {
  userId: string;
  onSuccess: (newDigest: Digest) => void;
  onError?: (errorMessage: string) => void;
  label?: string;
  variant?: "primary" | "secondary";
}

export const GenerateButton: React.FC<GenerateButtonProps> = ({
  userId,
  onSuccess,
  onError,
  label = "Generate My Weekly Digest",
  variant = "primary",
}) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<boolean>(false);

  const handleGenerate = async () => {
    setLoading(true);
    setErrorMsg(null);
    setSuccessToast(false);

    try {
      const result = await generateDigest(userId);
      onSuccess(result);
      setSuccessToast(true);
      setTimeout(() => {
        setSuccessToast(false);
      }, 3500);
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to generate digest. Please try again.";
      setErrorMsg(message);
      if (onError) {
        onError(message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="generate-btn-wrapper">
      <button
        onClick={handleGenerate}
        disabled={loading || !userId}
        className={`btn-generate ${variant === "secondary" ? "btn-secondary" : "btn-primary"} ${
          successToast ? "btn-success-flash" : ""
        }`}
      >
        {loading ? (
          <>
            <span className="spinner-icon-sm"></span>
            Analyzing activity & generating prose...
          </>
        ) : (
          <>
            <svg
              className="sparkle-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
            </svg>
            {label}
          </>
        )}
      </button>

      {successToast && (
        <div className="generate-success-toast">
          <span className="toast-icon">✓</span>
          <span>Digest regenerated successfully!</span>
        </div>
      )}

      {errorMsg && (
        <div className="generate-error-banner">
          <span className="error-icon">⚠️</span>
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
};
