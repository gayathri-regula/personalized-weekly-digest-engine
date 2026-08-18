import React, { useEffect, useState } from "react";
import {
  boostDigest,
  getDigest,
  getSavedItems,
  saveItem,
  submitFeedback,
  unsaveItem,
} from "../api/client";
import { Digest, DigestItem, User } from "../types";
import { groupDigestItems } from "../utils/groupDigestItems";
import { CategoryHighlights } from "./CategoryHighlights";
import { GenerateButton } from "./GenerateButton";
import { HeroDigestCard } from "./HeroDigestCard";
import { RightSidebar } from "./RightSidebar";
import { StoryList } from "./StoryList";

interface DigestViewProps {
  user: User | null;
  onOpenDrawer: () => void;
  onOpenEditInterests: () => void;
  onShowToast: (message: string) => void;
  onUserUpdated?: (updatedUser: User) => void;
}

export const DigestView: React.FC<DigestViewProps> = ({
  user,
  onOpenDrawer,
  onOpenEditInterests,
  onShowToast,
  onUserUpdated,
}) => {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [isNotFound, setIsNotFound] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Category filter state
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Boost interaction state
  const [boostedItems, setBoostedItems] = useState<DigestItem[] | null>(null);
  const [activeBoostTag, setActiveBoostTag] = useState<string | null>(null);
  const [boostingTag, setBoostingTag] = useState<string | null>(null);
  const [boostError, setBoostError] = useState<string | null>(null);

  // Local feedback state map: activityItemId -> feedback_type
  const [feedbackState, setFeedbackState] = useState<Record<string, string>>({});

  // Client-side save / bookmark state map: activityItemId -> boolean
  const [savedItemIds, setSavedItemIds] = useState<Record<string, boolean>>({});

  const toggleSaveItem = async (itemId: string) => {
    if (!user) return;
    const isCurrentlySaved = !!savedItemIds[itemId];
    const nextSavedState = !isCurrentlySaved;

    // Optimistically update local UI state immediately
    setSavedItemIds((prev) => ({
      ...prev,
      [itemId]: nextSavedState,
    }));

    try {
      if (nextSavedState) {
        await saveItem(user.id, itemId);
      } else {
        await unsaveItem(user.id, itemId);
      }
    } catch (err: unknown) {
      console.error("Failed to persist save state:", err);
      // Rollback local state on error
      setSavedItemIds((prev) => ({
        ...prev,
        [itemId]: isCurrentlySaved,
      }));
    }
  };

  useEffect(() => {
    // Reset boost and filter state when user changes
    setBoostedItems(null);
    setActiveBoostTag(null);
    setBoostingTag(null);
    setBoostError(null);
    setSelectedCategory(null);

    if (!user) {
      setDigest(null);
      setSavedItemIds({});
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
    setSelectedCategory(null);
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

  // Synchronize feedbackState when digest items load or update
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

  // Synchronize savedItemIds from backend when user or digest loads or updates
  useEffect(() => {
    if (user && digest) {
      let isSubscribed = true;
      getSavedItems(user.id)
        .then((savedItems) => {
          if (!isSubscribed) return;
          const savedMap: Record<string, boolean> = {};
          savedItems.forEach((s) => {
            savedMap[s.activity_item_id] = true;
          });
          setSavedItemIds(savedMap);
        })
        .catch((err) => {
          console.error("Failed to fetch saved items for digest sync:", err);
        });

      return () => {
        isSubscribed = false;
      };
    } else {
      setSavedItemIds({});
    }
  }, [user, digest]);

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

  return (
    <div className="redesign-dashboard-grid">
      {/* Center Main Content Column */}
      <div className="redesign-main-column">
        {!user ? (
          <div className="digest-empty-placeholder">
            <div className="placeholder-icon">👤</div>
            <h3>No User Profile Selected</h3>
            <p>
              Please select a user profile from the left sidebar or controls above to view their weekly digest.
            </p>
            <button
              type="button"
              className="btn-select-profile-lg"
              onClick={onOpenDrawer}
            >
              Select Profile Controls
            </button>
          </div>
        ) : loading ? (
          <div className="digest-loading-skeleton">
            <div className="skeleton-line skeleton-title"></div>
            <div className="skeleton-card skeleton-prose"></div>
            <div className="skeleton-card skeleton-item"></div>
            <div className="skeleton-card skeleton-item"></div>
          </div>
        ) : errorMessage ? (
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
        ) : isNotFound || !digest ? (
          <div className="digest-not-found-card">
            <div className="not-found-badge">No Digest Pending</div>
            <h2>Weekly Digest for {user.name} Not Yet Generated</h2>
            <p>
              We haven't compiled a digest for <strong>{user.name}</strong> for the current target week yet. Click below to generate their personalized weekly digest.
            </p>
            <GenerateButton
              userId={user.id}
              onSuccess={handleGeneratedSuccess}
              label="Compile Weekly Digest Now"
            />
          </div>
        ) : (
          <>
            {/* Hero Digest Card */}
            <HeroDigestCard
              user={user}
              digest={digest}
              onSuccess={handleGeneratedSuccess}
            />

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

            {/* Category Highlights */}
            {(() => {
              const itemsToDisplay =
                boostedItems !== null ? boostedItems : digest.items;
              const sections = groupDigestItems(itemsToDisplay);

              return (
                <>
                  <CategoryHighlights
                    sections={sections}
                    selectedCategory={selectedCategory}
                    onSelectCategory={setSelectedCategory}
                  />

                  {/* Top Stories For You Feed */}
                  <StoryList
                    sections={sections}
                    selectedCategory={selectedCategory}
                    feedbackState={feedbackState}
                    savedItemIds={savedItemIds}
                    onFeedbackClick={handleFeedbackClick}
                    onToggleSave={toggleSaveItem}
                  />
                </>
              );
            })()}

            {/* AI Suggestions Section */}
            {digest.ai_suggestions && digest.ai_suggestions.length > 0 && (
              <section className="redesign-ai-suggestions-section">
                <div className="suggestions-header-bar">
                  <div className="suggestions-title-group">
                    <h3 className="suggestions-main-heading">
                      🤖 AI Suggestions - Exploratory topics you might like
                    </h3>
                    <span className="badge-ai-subnote">
                      AI-generated • Click card to boost items
                    </span>
                  </div>
                </div>

                <div className="suggestions-cards-grid">
                  {digest.ai_suggestions.map((suggestion, idx) => {
                    const isBoostingThis = boostingTag === suggestion.related_tag;
                    const isActive = activeBoostTag === suggestion.related_tag;

                    return (
                      <article
                        key={idx}
                        className={`ai-suggestion-tile ${
                          isActive ? "is-active-boost" : ""
                        } ${isBoostingThis ? "is-loading-boost" : ""}`}
                        onClick={() =>
                          handleSuggestionClick(suggestion.related_tag)
                        }
                        role="button"
                        tabIndex={0}
                      >
                        <div className="suggestion-tile-header">
                          <span className="sparkle-icon-sm">✨</span>
                          <h4 className="suggestion-tile-title">
                            {suggestion.title}
                          </h4>
                          {suggestion.related_tag && (
                            <span className="suggestion-tag-chip">
                              ⚡ {suggestion.related_tag}
                            </span>
                          )}
                        </div>
                        <p className="suggestion-tile-desc">
                          {suggestion.description}
                        </p>

                        <div className="suggestion-tile-footer">
                          {isBoostingThis ? (
                            <span className="boosting-indicator-text">
                              <span className="spinner-icon-sm"></span> Boosting...
                            </span>
                          ) : isActive ? (
                            <span className="active-boost-text">
                              ✓ Currently Boosting
                            </span>
                          ) : (
                            <span className="hint-click-boost">
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
          </>
        )}
      </div>

      {/* Right Panel Sidebar Column */}
      <RightSidebar
        user={user}
        digest={digest}
        onOpenEditInterests={onOpenEditInterests}
        onShowToast={onShowToast}
        onUserUpdated={onUserUpdated}
      />
    </div>
  );
};
