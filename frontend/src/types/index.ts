/**
 * TypeScript type definitions matching the backend API contracts.
 */

export interface User {
  id: string;
  name: string;
  interest_tags: string[];
}

export interface UsersListResponse {
  users: User[];
}

export interface InterestsResponse {
  interests: string[];
}

export interface CreateUserPayload {
  name: string;
  interest_tags: string[];
}

export interface DigestItem {
  id: string;
  activity_item_id: string;
  title: string;
  content: string;
  category_tags: string[];
  relevance_score: number;
  explanation_text: string;
  rank_position: number;
}

export interface AISuggestion {
  title: string;
  description: string;
}

export interface Digest {
  id: string;
  user_id: string;
  week_identifier: string;
  generated_at: string;
  summary_prose: string;
  items: DigestItem[];
  ai_suggestions?: AISuggestion[];
}

export interface ApiFetchResult<T> {
  data: T | null;
  status: number;
  error: string | null;
  isNotFound: boolean;
}
