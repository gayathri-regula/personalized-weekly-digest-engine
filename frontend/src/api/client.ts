import { Digest, User, UsersListResponse } from "../types";

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  "http://127.0.0.1:8000";

/**
 * Custom Error class for API network and HTTP failures.
 */
export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Fetch all available users from the platform backend.
 */
export async function getUsers(): Promise<User[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users`);
    if (!response.ok) {
      throw new ApiError(
        `Failed to fetch users: HTTP ${response.status} ${response.statusText}`,
        response.status
      );
    }
    const data: UsersListResponse = await response.json();
    return data.users || [];
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      "Unable to connect to backend server. Please verify backend service is running.",
      0
    );
  }
}

/**
 * Fetch the latest weekly digest for a given user.
 * Returns null if status is 404 (digest not yet generated for user).
 */
export async function getDigest(userId: string): Promise<Digest | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/digest/${userId}`);
    if (response.status === 404) {
      // 404 is an expected state indicating no digest exists yet
      return null;
    }
    if (!response.ok) {
      throw new ApiError(
        `Failed to fetch digest for user '${userId}': HTTP ${response.status}`,
        response.status
      );
    }
    const data: Digest = await response.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      "Unable to connect to backend server. Please check your network connection.",
      0
    );
  }
}

/**
 * Trigger on-demand generation (or regeneration) of a weekly digest for a user.
 */
export async function generateDigest(userId: string): Promise<Digest> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/digest/${userId}`, {
      method: "POST",
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const detail = errData.detail || `HTTP ${response.status}`;
      throw new ApiError(
        `Failed to generate digest: ${detail}`,
        response.status
      );
    }
    const data: Digest = await response.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      "Backend server unreachable during digest generation. Please try again.",
      0
    );
  }
}
