import {
  BoostedDigest,
  Digest,
  FeedbackResponse,
  InterestsResponse,
  User,
  UsersListResponse,
} from "../types";

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
 * Fetch domain interest taxonomy from backend.
 */
export async function getInterests(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/interests`);
    if (!response.ok) {
      throw new ApiError(
        `Failed to fetch interests taxonomy: HTTP ${response.status}`,
        response.status
      );
    }
    const data: InterestsResponse = await response.json();
    return data.interests || [];
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
 * Register a new user profile on the backend.
 */
export async function createUser(
  name: string,
  interestTags: string[]
): Promise<User> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
        interest_tags: interestTags,
      }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const detail = errData.detail || `HTTP ${response.status}`;
      throw new ApiError(
        `Failed to create profile: ${detail}`,
        response.status
      );
    }
    const newUser: User = await response.json();
    return newUser;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      "Backend server unreachable during user creation. Please try again.",
      0
    );
  }
}

/**
 * Update interest tags for an existing user profile.
 */
export async function updateUserInterests(
  userId: string,
  interestTags: string[]
): Promise<User> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        interest_tags: interestTags,
      }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const detail = errData.detail || `HTTP ${response.status}`;
      throw new ApiError(
        `Failed to update interest topics: ${detail}`,
        response.status
      );
    }
    const updatedUser: User = await response.json();
    return updatedUser;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      "Backend server unreachable during profile update. Please try again.",
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
 * Supports legacy boolean `diversity` or explicit mode string ("standard" | "diverse" | "ai").
 */
export async function generateDigest(
  userId: string,
  diversityOrMode: boolean | "standard" | "diverse" | "ai" = false
): Promise<Digest> {
  try {
    let queryParam = "";
    if (diversityOrMode === true || diversityOrMode === "diverse") {
      queryParam = "?diversity=true";
    } else if (diversityOrMode === "ai") {
      queryParam = "?mode=ai";
    }

    const url = `${API_BASE_URL}/api/digest/${userId}${queryParam}`;
    const response = await fetch(url, {
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

/**
 * Temporarily boost digest items by a specific taxonomy tag.
 */
export async function boostDigest(
  userId: string,
  tag: string
): Promise<BoostedDigest> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/digest/${userId}/boost`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ tag }),
      }
    );

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const detail = errData.detail || `HTTP ${response.status}`;
      throw new ApiError(
        `Failed to boost digest items: ${detail}`,
        response.status
      );
    }
    const data: BoostedDigest = await response.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      "Backend server unreachable during digest boost. Please try again.",
      0
    );
  }
}

/**
 * Submit explicit user feedback rating for a digest activity item.
 */
export async function submitFeedback(
  userId: string,
  itemId: string,
  feedbackType: string
): Promise<FeedbackResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/feedback/${userId}/${itemId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ feedback_type: feedbackType }),
      }
    );

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const detail = errData.detail || `HTTP ${response.status}`;
      throw new ApiError(
        `Failed to submit feedback: ${detail}`,
        response.status
      );
    }
    const data: FeedbackResponse = await response.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      "Backend server unreachable during feedback submission.",
      0
    );
  }
}

