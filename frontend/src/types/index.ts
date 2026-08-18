/**
 * TypeScript type definitions matching the backend API contracts.
 */

export interface User {
  id: string;
  name: string;
  interest_tags: string[];
  digest_frequency?: string;
  content_length?: string;
  digest_language?: string;
}

export interface UserPreferencesPayload {
  digest_frequency?: string;
  content_length?: string;
  digest_language?: string;
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

export interface FeedbackResponse {
  id: string;
  user_id: string;
  activity_item_id: string;
  feedback_type: string;
  created_at: string;
}

export interface DigestItem {
  id: string;
  activity_item_id: string;
  title: string;
  content: string;
  category_tags: string[];
  section_title?: string;
  relevance_score: number;
  explanation_text: string;
  rank_position: number;
  feedback_type?: string | null;
  created_at?: string;
}

export interface AISuggestion {
  title: string;
  description: string;
  related_tag: string;
}

export interface BoostedDigest {
  boost_tag: string;
  items: DigestItem[];
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

export interface SavedItemResponse {
  id: string;
  user_id: string;
  activity_item_id: string;
  created_at: string;
}

export interface SavedItemDetail {
  id: string;
  user_id: string;
  activity_item_id: string;
  title: string;
  content: string;
  category_tags: string[];
  section_title?: string | null;
  explanation_text?: string | null;
  created_at?: string | null;
  saved_at: string;
}

export interface ActivityLogEntry {
  id: string;
  user_id: string;
  event_type: string;
  description: string;
  created_at: string;
}

export interface ActivityLogListResponse {
  items: ActivityLogEntry[];
  total: number;
}

export interface ShareLinkResponse {
  share_token: string;
  share_url: string;
}

export interface SharedDigestItem {
  id: string;
  activity_item_id: string;
  title: string;
  content: string;
  category_tags: string[];
  section_title?: string | null;
  relevance_score: number;
  explanation_text: string;
  rank_position: number;
  created_at?: string | null;
}

export interface SharedDigest {
  user_name: string;
  week_identifier: string;
  generated_at: string;
  summary_prose: string;
  items: SharedDigestItem[];
  ai_suggestions?: AISuggestion[];
}


