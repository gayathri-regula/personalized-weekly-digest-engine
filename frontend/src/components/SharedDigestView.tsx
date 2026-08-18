import React, { useEffect, useState } from "react";
import { getSharedDigest } from "../api/client";
import { SharedDigest } from "../types";
import { renderMarkdownProse } from "./HeroDigestCard";

interface SharedDigestViewProps {
  token: string;
}

export const SharedDigestView: React.FC<SharedDigestViewProps> = ({ token }) => {
  const [digest, setDigest] = useState<SharedDigest | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isSubscribed = true;
    const fetchDigest = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getSharedDigest(token);
        if (isSubscribed) {
          setDigest(data);
        }
      } catch (err: unknown) {
        if (isSubscribed) {
          const msg =
            err instanceof Error ? err.message : "Failed to load shared digest.";
          setError(msg);
        }
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
  }, [token]);

  return (
    <div className="shared-digest-page-shell">
      {/* Top Header Bar for Public Shared View */}
      <header className="shared-page-header">
        <div className="shared-header-inner">
          <div className="shared-brand">
            <span className="shared-brand-icon">📰</span>
            <span className="shared-brand-title">Personalized Weekly Digest Engine</span>
            <span className="shared-public-badge">Public Shared View</span>
          </div>
          <button
            type="button"
            className="btn-go-to-app"
            onClick={() => (window.location.href = "/")}
          >
            Go to Main App ↗
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="shared-digest-container">
        {loading ? (
          <div className="shared-loading-card">
            <div className="shared-spinner">⏳</div>
            <p className="shared-loading-text">Loading shared digest preview...</p>
          </div>
        ) : error ? (
          <div className="shared-error-card">
            <span className="shared-error-icon">🔒</span>
            <h2 className="shared-error-title">Digest Unavailable</h2>
            <p className="shared-error-desc">{error}</p>
            <button
              type="button"
              className="btn-shared-home"
              onClick={() => (window.location.href = "/")}
            >
              Return to Home Dashboard
            </button>
          </div>
        ) : digest ? (
          <div className="shared-digest-content">
            {/* Digest Meta Header Banner */}
            <div className="shared-meta-card">
              <div className="shared-meta-top">
                <span className="shared-user-name">👤 {digest.user_name}'s Digest</span>
                <span className="shared-week-tag">📅 Week {digest.week_identifier}</span>
                <span className="shared-readonly-chip">👁️ Read-Only</span>
              </div>
              <p className="shared-meta-time">
                Generated on{" "}
                {new Date(digest.generated_at).toLocaleDateString(undefined, {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            </div>

            {/* Executive Summary Prose Card */}
            <div className="shared-summary-card">
              <div className="shared-summary-header">
                <span className="summary-header-icon">✨</span>
                <h3>Executive Summary</h3>
              </div>
              <div className="shared-summary-body">{renderMarkdownProse(digest.summary_prose)}</div>
            </div>

            {/* Ranked Stories List */}
            <div className="shared-stories-section">
              <div className="shared-stories-header">
                <h3>Top Ranked Stories ({digest.items.length})</h3>
                <span className="shared-stories-sub">Personalized based on user focus topics</span>
              </div>

              <div className="shared-stories-list">
                {digest.items.map((item) => (
                  <div key={item.id} className="shared-story-card">
                    <div className="shared-story-top">
                      <span className="shared-rank-badge">#{item.rank_position}</span>
                      {item.section_title && (
                        <span className="shared-section-tag">{item.section_title}</span>
                      )}
                      <span className="shared-score-pill">
                        🎯 {Math.round(item.relevance_score * 100)}% match
                      </span>
                    </div>

                    <h4 className="shared-story-title">{item.title}</h4>

                    {item.category_tags && item.category_tags.length > 0 && (
                      <div className="shared-tags-row">
                        {item.category_tags.map((tag) => (
                          <span key={tag} className="shared-tag-chip">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}

                    <p className="shared-story-content">{item.content}</p>

                    <div className="shared-explanation-box">
                      <span className="explanation-icon">💡</span>
                      <span className="explanation-text">{item.explanation_text}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Exploratory Suggestions (if present) */}
            {digest.ai_suggestions && digest.ai_suggestions.length > 0 && (
              <div className="shared-suggestions-card">
                <div className="shared-suggestions-header">
                  <span className="suggestions-header-icon">🔮</span>
                  <h3>AI Exploratory Topic Suggestions</h3>
                </div>
                <div className="shared-suggestions-grid">
                  {digest.ai_suggestions.map((sug, idx) => (
                    <div key={idx} className="shared-suggestion-item">
                      <h5 className="sug-title">{sug.title}</h5>
                      <p className="sug-desc">{sug.description}</p>
                      {sug.related_tag && (
                        <span className="sug-tag">Related: #{sug.related_tag}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Read-Only Footer Note */}
            <footer className="shared-digest-footer">
              <p>
                This is a public, read-only preview of a Weekly Digest generated by{" "}
                <strong>Personalized Weekly Digest Engine</strong>.
              </p>
            </footer>
          </div>
        ) : null}
      </main>
    </div>
  );
};
