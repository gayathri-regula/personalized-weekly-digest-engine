import React, { useEffect, useState } from "react";
import { getDigest } from "../api/client";
import { Digest, User } from "../types";
import { GenerateButton } from "./GenerateButton";

interface DigestViewProps {
  user: User | null;
}

export const DigestView: React.FC<DigestViewProps> = ({ user }) => {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [isNotFound, setIsNotFound] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
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

  return (
    <div className="digest-view-container">
      {/* Digest Header */}
      <header className="digest-header">
        <div className="header-titles">
          <span className="week-badge">Week {digest.week_identifier}</span>
          <h1 className="greeting-heading">
            Hi {user.name.split(" ")[0]}, here is your weekly digest
          </h1>
          <p className="timestamp-subtitle">
            Generated on {new Date(digest.generated_at).toLocaleDateString(undefined, {
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
          <span className="count-badge">{digest.items.length} Items</span>
        </div>

        {digest.items.length === 0 ? (
          <div className="no-items-card">
            <p>No highly relevant activity updates were found for your interest topics this week.</p>
          </div>
        ) : (
          <div className="items-grid">
            {digest.items.map((item) => {
              const relevancePercent = Math.round(item.relevance_score * 100);

              return (
                <article key={item.id} className="digest-item-card">
                  <div className="item-card-top">
                    <span className="rank-pill">#{item.rank_position}</span>
                    <div className="relevance-meter">
                      <div
                        className="relevance-fill"
                        style={{ width: `${relevancePercent}%` }}
                      ></div>
                      <span className="relevance-label">{relevancePercent}% Match</span>
                    </div>
                  </div>

                  <h3 className="item-title">{item.title}</h3>
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
              <span className="badge-ai-note">AI-generated, not from your ranked feed</span>
            </div>
          </div>

          <div className="suggestions-grid">
            {digest.ai_suggestions.map((suggestion, idx) => (
              <article key={idx} className="ai-suggestion-card">
                <div className="suggestion-card-header">
                  <span className="sparkle-icon">✨</span>
                  <h3 className="suggestion-title">{suggestion.title}</h3>
                </div>
                <p className="suggestion-description">{suggestion.description}</p>
              </article>
            ))}
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
