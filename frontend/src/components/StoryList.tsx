import React from "react";
import { DigestSection } from "../utils/groupDigestItems";
import { getCategoryTheme } from "../utils/categoryIcons";

interface StoryListProps {
  sections: DigestSection[];
  selectedCategory: string | null;
  feedbackState: Record<string, string>;
  savedItemIds: Record<string, boolean>;
  onFeedbackClick: (activityItemId: string, type: string) => void;
  onToggleSave: (itemId: string) => void;
}

export const StoryList: React.FC<StoryListProps> = ({
  sections,
  selectedCategory,
  feedbackState,
  savedItemIds,
  onFeedbackClick,
  onToggleSave,
}) => {
  const filteredSections = selectedCategory
    ? sections.filter((s) => s.id === selectedCategory)
    : sections;

  const totalFilteredCount = filteredSections.reduce(
    (acc, sec) => acc + sec.items.length,
    0
  );

  return (
    <section className="redesign-top-stories-section">
      {/* Section Title Header */}
      <div className="stories-section-header">
        <div className="stories-title-group">
          <span className="stories-star-icon">✨</span>
          <h3 className="stories-main-heading">Top Stories For You</h3>
          <span className="stories-count-badge">{totalFilteredCount} Stories</span>
        </div>
      </div>

      {totalFilteredCount === 0 ? (
        <div className="empty-stories-box">
          <p>No stories found for the selected category filter.</p>
        </div>
      ) : (
        <div className="story-sections-list">
          {filteredSections.map((section) => (
            <div key={section.id} className="story-section-block">
              <div className="story-section-title-bar">
                <h4 className="story-section-title-text">
                  {section.id === "top-picks" ? "⭐ Top Picks" : `📌 ${section.title}`}
                </h4>
                <span className="story-section-item-count">
                  {section.items.length} {section.items.length === 1 ? "item" : "items"}
                </span>
              </div>

              <div className="story-cards-wrapper">
                {section.items.map((item) => {
                  const relevancePercent = Math.round(item.relevance_score * 100);
                  const theme = getCategoryTheme(
                    item.section_title || item.category_tags[0]
                  );
                  const isSaved = !!savedItemIds[item.activity_item_id];
                  const currentFeedback = feedbackState[item.activity_item_id];

                  return (
                    <article
                      key={item.id}
                      className={`redesign-story-card ${isSaved ? "is-bookmarked" : ""}`}
                    >
                      {/* Dynamic Light Category Icon Thumbnail Tile */}
                      <div
                        className="story-thumbnail-tile"
                        style={{
                          background: theme.gradient,
                          borderRight: `1px solid ${theme.borderColor}`,
                        }}
                      >
                        <span className="thumbnail-icon-large">{theme.icon}</span>
                        <span className="thumbnail-tag-label">
                          {item.category_tags[0] || "General"}
                        </span>
                        <span className="thumbnail-rank-badge">
                          #{item.rank_position}
                        </span>
                      </div>

                      {/* Story Body Content */}
                      <div className="story-body-content">
                        <div className="story-body-header">
                          <h4 className="story-heading-title">{item.title}</h4>
                          <div className="relevance-match-badge">
                            <span className="match-percent">{relevancePercent}%</span>
                            <span className="match-label">Match</span>
                          </div>
                        </div>

                        <p className="story-text-body">{item.content}</p>

                        {/* Transparency Explanation Reason */}
                        <div className="transparency-reason-box">
                          <span className="transparency-bulb-icon">💡</span>
                          <span className="transparency-reason-text">
                            {item.explanation_text}
                          </span>
                        </div>

                        {/* Category Tags */}
                        {item.category_tags && item.category_tags.length > 0 && (
                          <div className="story-category-chips">
                            {item.category_tags.map((tag) => (
                              <span key={tag} className="story-chip">
                                #{tag}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Feedback & Bookmark Actions */}
                        <div className="story-footer-actions">
                          <div className="feedback-btns-row">
                            <button
                              type="button"
                              className={`btn-feedback-action useful ${
                                currentFeedback === "useful" ? "is-active" : ""
                              }`}
                              onClick={() =>
                                onFeedbackClick(item.activity_item_id, "useful")
                              }
                              title="Mark as Useful"
                            >
                              👍 Useful
                            </button>
                            <button
                              type="button"
                              className={`btn-feedback-action not-useful ${
                                currentFeedback === "not_useful" ? "is-active" : ""
                              }`}
                              onClick={() =>
                                onFeedbackClick(item.activity_item_id, "not_useful")
                              }
                              title="Mark as Not Useful"
                            >
                              👎 Not Useful
                            </button>
                            <button
                              type="button"
                              className={`btn-feedback-action not-interested ${
                                currentFeedback === "not_interested" ? "is-active" : ""
                              }`}
                              onClick={() =>
                                onFeedbackClick(item.activity_item_id, "not_interested")
                              }
                              title="Mark as Not Interested"
                            >
                              🚫 Not Interested
                            </button>
                          </div>

                          <button
                            type="button"
                            className={`btn-save-action ${isSaved ? "is-saved" : ""}`}
                            onClick={() => onToggleSave(item.activity_item_id)}
                            title={isSaved ? "Remove from Saved" : "Save story"}
                          >
                            {isSaved ? "🔖 Saved" : "🔖 Save"}
                          </button>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
};
