import React, { useEffect, useState } from "react";
import { getSavedItems, unsaveItem } from "../api/client";
import { SavedItemDetail, User } from "../types";
import { getCategoryTheme } from "../utils/categoryIcons";

interface SavedItemsViewProps {
  user: User | null;
  onOpenDrawer: () => void;
}

export const SavedItemsView: React.FC<SavedItemsViewProps> = ({
  user,
  onOpenDrawer,
}) => {
  const [items, setItems] = useState<SavedItemDetail[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSaved = async () => {
    if (!user) {
      setItems([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getSavedItems(user.id);
      setItems(data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to load saved items.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSaved();
  }, [user]);

  const handleUnsave = async (activityItemId: string) => {
    if (!user) return;
    // Optimistic UI update
    setItems((prev) => prev.filter((item) => item.activity_item_id !== activityItemId));
    try {
      await unsaveItem(user.id, activityItemId);
    } catch (err: unknown) {
      console.error("Failed to unsave item:", err);
      // Rollback by refreshing list
      fetchSaved();
    }
  };

  if (!user) {
    return (
      <div className="saved-empty-container">
        <div className="placeholder-icon">👤</div>
        <h3>No User Profile Selected</h3>
        <p>Please select a user profile to view their saved reading list.</p>
        <button
          type="button"
          className="btn-select-profile-lg"
          onClick={onOpenDrawer}
        >
          Select Profile Controls
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="saved-items-view">
        <div className="saved-items-header">
          <div className="saved-title-group">
            <span className="saved-header-icon">🔖</span>
            <h2 className="saved-main-heading">Saved Reading List</h2>
            <span className="saved-count-badge">Loading...</span>
          </div>
        </div>
        <div className="digest-loading-skeleton">
          <div className="skeleton-card skeleton-item"></div>
          <div className="skeleton-card skeleton-item"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="saved-items-view">
        <div className="digest-error-card">
          <div className="error-card-header">
            <span className="error-badge-lg">Server Error</span>
            <h3>Couldn't fetch saved reading list</h3>
          </div>
          <p>{error}</p>
          <button onClick={fetchSaved} className="btn-retry-lg">
            Try Reloading
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="saved-items-view">
      <div className="saved-items-header">
        <div className="saved-title-group">
          <span className="saved-header-icon">🔖</span>
          <h2 className="saved-main-heading">Saved Reading List</h2>
          <span className="saved-count-badge">
            {items.length} {items.length === 1 ? "Item" : "Items"}
          </span>
        </div>
      </div>

      {items.length === 0 ? (
        <div className="saved-empty-box">
          <span className="saved-empty-icon">📚</span>
          <h3>No saved items yet</h3>
          <p>
            Click the 🔖 <strong>Save</strong> button on any story in your weekly digest to bookmark it here for quick reading later.
          </p>
        </div>
      ) : (
        <div className="saved-cards-list">
          {items.map((item) => {
            const theme = getCategoryTheme(
              item.section_title || (item.category_tags && item.category_tags[0]) || "General"
            );
            return (
              <article key={item.id} className="redesign-story-card is-bookmarked">
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
                    {item.category_tags && item.category_tags[0] ? item.category_tags[0] : "General"}
                  </span>
                </div>

                {/* Story Body Content */}
                <div className="story-body-content">
                  <div className="story-body-header">
                    <h4 className="story-heading-title">{item.title}</h4>
                    <span className="saved-at-date">
                      Saved {new Date(item.saved_at).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="story-text-body">{item.content}</p>

                  {/* Transparency Explanation Reason */}
                  {item.explanation_text && (
                    <div className="transparency-reason-box">
                      <span className="transparency-bulb-icon">💡</span>
                      <span className="transparency-reason-text">
                        {item.explanation_text}
                      </span>
                    </div>
                  )}

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

                  {/* Footer Action */}
                  <div className="story-footer-actions">
                    <button
                      type="button"
                      className="btn-save-action is-saved"
                      onClick={() => handleUnsave(item.activity_item_id)}
                      title="Remove story from saved list"
                    >
                      🔖 Unsave
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
};
