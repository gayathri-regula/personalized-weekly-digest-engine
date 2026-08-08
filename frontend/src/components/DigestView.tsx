import React, { useEffect, useState } from "react";
import { boostDigest, getDigest, submitFeedback } from "../api/client";
import { Digest, DigestItem, User } from "../types";
import { GenerateButton } from "./GenerateButton";

interface DigestViewProps {
  user: User | null;
}

function formatRelativeTime(dateStr?: string): string | null {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return null;
  const refNow = new Date("2026-07-25T12:00:00Z");
  const diffMs = refNow.getTime() - date.getTime();
  if (diffMs < 0) return "Recently";
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return "Just now";
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays === 1) return "1 day ago";
  return `${diffDays} days ago`;
}

export const DigestView: React.FC<DigestViewProps> = ({ user }) => {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [isNotFound, setIsNotFound] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Boost interaction state
  const [boostedItems, setBoostedItems] = useState<DigestItem[] | null>(null);
  const [activeBoostTag, setActiveBoostTag] = useState<string | null>(null);
  const [boostingTag, setBoostingTag] = useState<string | null>(null);
  const [boostError, setBoostError] = useState<string | null>(null);

  // Local feedback state map: activityItemId -> feedback_type ("useful" | "not_useful" | "not_interested")
  const [feedbackState, setFeedbackState] = useState<Record<string, string>>({});

  // Client-side save / bookmark state map: activityItemId -> boolean
  const [savedItemIds, setSavedItemIds] = useState<Record<string, boolean>>({});

  const toggleSaveItem = (itemId: string) => {
    setSavedItemIds((prev) => ({
      ...prev,
      [itemId]: !prev[itemId],
    }));
  };

  useEffect(() => {
    // Reset boost state when user changes
    setBoostedItems(null);
    setActiveBoostTag(null);
    setBoostingTag(null);
    setBoostError(null);

    if (!user) {
      setDigest(null);
      setIsNotFound(false);
      setErrorMessage(null);
      return;
    }

    let isSubscribed = true;
    const fetchDigest = async () => {
      setLoading(true);
      setIsNotFound(false);
      setErrorMessage(null);
      try {
        const result = await getDigest(user.id);
        if (!isSubscribed) return;

        if (result === null) {
          setIsNotFound(true);
          setDigest(null);
        } else {
          setDigest(result);
          setIsNotFound(false);
        }
      } catch (err: unknown) {
        if (!isSubscribed) return;
        const msg =
          err instanceof Error
            ? err.message
            : "Failed to load digest from server.";
        setErrorMessage(msg);
      } finally {
        if (isSubscribed) {
          setLoading(false);
        }
      }
    };

    fetchDigest();

    return () => {
      isSubscribed = false;
    };
  }, [user]);

  const handleGeneratedSuccess = (newDigest: Digest) => {
    setDigest(newDigest);
    setIsNotFound(false);
    setErrorMessage(null);
    setBoostedItems(null);
    setActiveBoostTag(null);
    setBoostingTag(null);
    setBoostError(null);
  };

  const handleSuggestionClick = async (tag: string) => {
    if (!user || boostingTag === tag) return;
    setBoostingTag(tag);
    setBoostError(null);
    try {
      const result = await boostDigest(user.id, tag);
      setActiveBoostTag(result.boost_tag);
      setBoostedItems(result.items);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to boost digest items.";
      setBoostError(msg);
    } finally {
      setBoostingTag(null);
    }
  };

  const handleResetBoost = () => {
    setActiveBoostTag(null);
    setBoostedItems(null);
    setBoostError(null);
  };

  // Synchronize local feedbackState when digest items load or update
  useEffect(() => {
    if (digest) {
      const initialMap: Record<string, string> = {};
      digest.items.forEach((item) => {
        if (item.feedback_type) {
          initialMap[item.activity_item_id] = item.feedback_type;
        }
      });
      setFeedbackState(initialMap);
    } else {
      setFeedbackState({});
    }
  }, [digest]);

  const handleFeedbackClick = async (
    activityItemId: string,
    selectedType: string
  ) => {
    if (!user) return;

    // Optimistically update local UI state
    setFeedbackState((prev) => ({
      ...prev,
      [activityItemId]: selectedType,
    }));

    try {
      await submitFeedback(user.id, activityItemId, selectedType);
    } catch (err: unknown) {
      console.error("Failed to persist feedback:", err);
    }
  };

  if (!user) {
    return (
      <div className="digest-empty-placeholder">
        <div className="placeholder-icon">👤</div>
        <h3>No User Profile Selected</h3>
        <p>Please select a team member profile above to view their weekly digest.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="digest-loading-skeleton">
        <div className="skeleton-line skeleton-title"></div>
        <div className="skeleton-card skeleton-prose"></div>
        <div className="skeleton-card skeleton-item"></div>
        <div className="skeleton-card skeleton-item"></div>
      </div>
    );
  }

  if (errorMessage) {
    return (
      <div className="digest-error-card">
        <div className="error-card-header">
          <span className="error-badge-lg">Server Error</span>
          <h3>Couldn't connect to Backend Engine</h3>
        </div>
        <p>{errorMessage}</p>
        <button
          onClick={() => {
            if (user) {
              setLoading(true);
              setErrorMessage(null);
              getDigest(user.id)
                .then((res) => {
                  if (res === null) setIsNotFound(true);
                  else setDigest(res);
                })
                .catch((e) => setErrorMessage(e.message))
                .finally(() => setLoading(false));
            }
          }}
          className="btn-retry-lg"
        >
          Try Reloading
        </button>
      </div>
    );
  }

  if (isNotFound || !digest) {
    return (
      <div className="digest-not-found-card">
        <div className="not-found-badge">No Digest Pending</div>
        <h2>Weekly Digest for {user.name} Not Yet Generated</h2>
        <p>
          We haven't compiled a digest for <strong>{user.name}</strong> for the current target week yet. Click below to trigger the personalized relevance ranker and AI prose summarizer.
        </p>
        <GenerateButton
          userId={user.id}
          onSuccess={handleGeneratedSuccess}
          label="Compile Weekly Digest Now"
        />
      </div>
    );
  }

  const itemsToDisplay = boostedItems !== null ? boostedItems : digest.items;
  const totalInterests = user.interest_tags ? user.interest_tags.length : 0;
  const itemsCount = itemsToDisplay.length;
  const avgMatchPercent =
    itemsCount > 0
      ? Math.round(
          (itemsToDisplay.reduce((acc, item) => acc + item.relevance_score, 0) /
            itemsCount) *
            100
        )
      : 0;

  return (
    <div className="digest-view-container">
      {/* Hero Intro Banner */}
      <div className="hero-intro-banner">
        <h1 className="hero-title">Your Weekly Digest</h1>
        <p className="hero-subtitle">
          AI-curated updates based on the topics you follow.
        </p>
      </div>

      {/* Digest Header */}
      <header className="digest-header">
        <div className="header-titles">
          <span className="week-badge">Week {digest.week_identifier}</span>
          <h1 className="greeting-heading">
            Hi {user.name.split(" ")[0]}, here is your weekly digest
          </h1>
          <p className="timestamp-subtitle">
            Generated on{" "}
            {new Date(digest.generated_at).toLocaleDateString(undefined, {
              weekday: "long",
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </p>
        </div>

        <GenerateButton
          userId={user.id}
          onSuccess={handleGeneratedSuccess}
          label="Regenerate Digest"
          variant="secondary"
        />
      </header>

      {/* Dashboard Stats Header */}
      <div className="dashboard-stats-row">
        <div className="stat-card">
          <span className="stat-label">Interests</span>
          <span className="stat-value">{totalInterests} Topics</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Recommendations</span>
          <span className="stat-value">{itemsCount} Items</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Avg. Match</span>
          <span className="stat-value">{avgMatchPercent}%</span>
        </div>
      </div>

      {/* Executive Summary Prose Section */}
      <section className="summary-prose-card">
        <div className="card-header-bar">
          <span className="section-icon">✨</span>
          <h2>Executive Summary Highlights</h2>
        </div>
        <div className="prose-body">{renderMarkdownProse(digest.summary_prose)}</div>
      </section>

      {/* Ranked Activity Items Section */}
      <section className="ranked-items-section">
        <div className="section-header">
          <h2>Top-Ranked Highlights for You</h2>
          <span className="count-badge">{itemsToDisplay.length} Items</span>
        </div>

        {/* Boost Banner */}
        {activeBoostTag && (
          <div className="boost-banner">
            <div className="boost-banner-info">
              <span className="boost-icon">⚡</span>
              <span>
                Showing items boosted by: <strong>{activeBoostTag}</strong>
              </span>
            </div>
            <button
              onClick={handleResetBoost}
              className="btn-reset-boost"
              title="Restore original digest"
            >
              Reset to my digest
            </button>
          </div>
        )}

        {boostError && (
          <div className="boost-error-banner">
            <span>⚠️ {boostError}</span>
          </div>
        )}

        {itemsToDisplay.length === 0 ? (
          <div className="no-items-card">
            <p>No highly relevant activity updates were found for your interest topics this week.</p>
          </div>
        ) : (
          <div className="items-grid">
            {itemsToDisplay.map((item) => {
              const relevancePercent = Math.round(item.relevance_score * 100);
              const relativeTime = formatRelativeTime(item.created_at);

              return (
                <article
                  key={item.id}
                  className={`digest-item-card ${
                    savedItemIds[item.activity_item_id] ? "card-is-saved" : ""
                  }`}
                >
                  <div className="item-card-header-row">
                    <span className="rank-pill">#{item.rank_position}</span>
                    <h3 className="item-title">{item.title}</h3>
                  </div>

                  <div className="item-meta-row">
                    {relativeTime && (
                      <span className="time-badge">🕒 {relativeTime}</span>
                    )}
                    <div className="relevance-meter">
                      <div
                        className="relevance-fill"
                        style={{ width: `${relevancePercent}%` }}
                      ></div>
                      <span className="relevance-label">{relevancePercent}% Match</span>
                    </div>
                  </div>

                  <p className="item-content">{item.content}</p>

                  {/* Core Transparency Explanation Badge */}
                  <div className="transparency-banner">
                    <span className="explanation-icon">💡</span>
                    <span className="explanation-text">{item.explanation_text}</span>
                  </div>

                  {item.category_tags && item.category_tags.length > 0 && (
                    <div className="item-tags-row">
                      {item.category_tags.map((tag) => (
                        <span key={tag} className="tag-chip">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Feedback Buttons & Save Action Row */}
                  <div className="item-actions-row">
                    <div className="item-feedback-row">
                      <button
                        type="button"
                        className={`feedback-btn feedback-useful ${
                          feedbackState[item.activity_item_id] === "useful" ? "active" : ""
                        }`}
                        onClick={() => handleFeedbackClick(item.activity_item_id, "useful")}
                        title="Mark as Useful"
                      >
                        👍 Useful
                      </button>
                      <button
                        type="button"
                        className={`feedback-btn feedback-not-useful ${
                          feedbackState[item.activity_item_id] === "not_useful" ? "active" : ""
                        }`}
                        onClick={() => handleFeedbackClick(item.activity_item_id, "not_useful")}
                        title="Mark as Not Useful"
                      >
                        👎 Not Useful
                      </button>
                      <button
                        type="button"
                        className={`feedback-btn feedback-not-interested ${
                          feedbackState[item.activity_item_id] === "not_interested" ? "active" : ""
                        }`}
                        onClick={() => handleFeedbackClick(item.activity_item_id, "not_interested")}
                        title="Mark as Not Interested"
                      >
                        🚫 Not Interested
                      </button>
                    </div>

                    <button
                      type="button"
                      className={`btn-save-bookmark ${
                        savedItemIds[item.activity_item_id] ? "saved" : ""
                      }`}
                      onClick={() => toggleSaveItem(item.activity_item_id)}
                      title={
                        savedItemIds[item.activity_item_id]
                          ? "Remove from Saved"
                          : "Save for later"
                      }
                    >
                      {savedItemIds[item.activity_item_id] ? "🔖 Saved" : "🔖 Save"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {/* AI Suggestions Section */}
      {digest.ai_suggestions && digest.ai_suggestions.length > 0 && (
        <section className="ai-suggestions-section">
          <div className="section-header suggestions-header">
            <div className="header-title-group">
              <h2>🤖 AI Suggestions - Exploratory topics you might also like</h2>
              <span className="badge-ai-note">AI-generated • Click card to boost items</span>
            </div>
          </div>

          <div className="suggestions-grid">
            {digest.ai_suggestions.map((suggestion, idx) => {
              const isBoostingThis = boostingTag === suggestion.related_tag;
              const isActive = activeBoostTag === suggestion.related_tag;

              return (
                <article
                  key={idx}
                  className={`ai-suggestion-card clickable ${
                    isActive ? "suggestion-card-active" : ""
                  } ${isBoostingThis ? "suggestion-card-loading" : ""}`}
                  onClick={() => handleSuggestionClick(suggestion.related_tag)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      handleSuggestionClick(suggestion.related_tag);
                    }
                  }}
                >
                  <div className="suggestion-card-header">
                    <span className="sparkle-icon">✨</span>
                    <h3 className="suggestion-title">{suggestion.title}</h3>
                    {suggestion.related_tag && (
                      <span className="suggestion-tag-pill">
                        ⚡ {suggestion.related_tag}
                      </span>
                    )}
                  </div>
                  <p className="suggestion-description">{suggestion.description}</p>

                  <div className="suggestion-card-footer">
                    {isBoostingThis ? (
                      <span className="boosting-indicator">
                        <span className="spinner-icon-sm-purple"></span> Boosting...
                      </span>
                    ) : isActive ? (
                      <span className="active-boost-indicator">
                        ✓ Currently Boosting
                      </span>
                    ) : (
                      <span className="click-boost-hint">
                        Click to preview boosted items →
                      </span>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
};

/**
 * Inline helper to parse basic markdown headers, lists, and inline bold/italic tags.
 */
function renderMarkdownProse(prose: string) {
  if (!prose) return null;

  const lines = prose.split("\n");
  const elements: React.ReactNode[] = [];
  let inList = false;
  let listItems: React.ReactNode[] = [];

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      if (inList) {
        elements.push(
          <ul key={`ul-${idx}`} className="prose-ul">
            {listItems}
          </ul>
        );
        inList = false;
        listItems = [];
      }
      return;
    }

    if (trimmed.startsWith("### ")) {
      if (inList) {
        elements.push(
          <ul key={`ul-${idx}`} className="prose-ul">
            {listItems}
          </ul>
        );
        inList = false;
        listItems = [];
      }
      elements.push(
        <h3 key={idx} className="prose-h3">
          {parseInlineFormatting(trimmed.substring(4))}
        </h3>
      );
    } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      inList = true;
      listItems.push(
        <li key={idx} className="prose-li">
          {parseInlineFormatting(trimmed.substring(2))}
        </li>
      );
    } else {
      if (inList) {
        elements.push(
          <ul key={`ul-${idx}`} className="prose-ul">
            {listItems}
          </ul>
        );
        inList = false;
        listItems = [];
      }
      elements.push(
        <p key={idx} className="prose-p">
          {parseInlineFormatting(trimmed)}
        </p>
      );
    }
  });

  if (inList) {
    elements.push(
      <ul key="ul-final" className="prose-ul">
        {listItems}
      </ul>
    );
  }

  return <div className="formatted-prose">{elements}</div>;
}

function parseInlineFormatting(text: string): React.ReactNode[] {
  // Regex to split by **bold**, *italic*, or `code`
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}
