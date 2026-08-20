import React, { useEffect, useRef, useState } from "react";
import { getActivityLog, getDigestVoice, getOrCreateShareLink, getTrendingTopics, updateUserPreferences } from "../api/client";
import { ActivityLogEntry, Digest, TrendingTopic, User } from "../types";
import { BookmarkIcon, HistoryIcon } from "./icons/NavIcons";

interface RightSidebarProps {
  user: User | null;
  digest: Digest | null;
  onOpenEditInterests: () => void;
  onShowToast: (message: string) => void;
  onUserUpdated?: (updatedUser: User) => void;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({
  user,
  digest,
  onOpenEditInterests,
  onShowToast,
  onUserUpdated,
}) => {
  const [recentActivities, setRecentActivities] = useState<ActivityLogEntry[]>([]);
  const [loadingActivity, setLoadingActivity] = useState<boolean>(false);

  // Digest Preferences state
  const [frequency, setFrequency] = useState<string>("weekly");
  const [contentLength, setContentLength] = useState<string>("detailed");
  const [language, setLanguage] = useState<string>("en");
  const [savingPrefs, setSavingPrefs] = useState<boolean>(false);
  const [prefError, setPrefError] = useState<string | null>(null);
  const [shareUrl, setShareUrl] = useState<string>("");
  const [copyingShare, setCopyingShare] = useState<boolean>(false);

  // Voice Digest audio state
  const [loadingVoice, setLoadingVoice] = useState<boolean>(false);
  const [isPlayingVoice, setIsPlayingVoice] = useState<boolean>(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  // Trending Topics state
  const [trendingTopics, setTrendingTopics] = useState<TrendingTopic[]>([]);
  const [loadingTrending, setLoadingTrending] = useState<boolean>(false);

  useEffect(() => {
    // Reset and cleanup audio when selected user or digest changes
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
    setIsPlayingVoice(false);
    setLoadingVoice(false);

    if (user) {
      setFrequency(user.digest_frequency || "weekly");
      setContentLength(user.content_length || "detailed");
      setLanguage(user.digest_language || "en");
      setShareUrl("");

      setLoadingTrending(true);
      getTrendingTopics(user.id)
        .then((data) => setTrendingTopics(data))
        .catch(() => setTrendingTopics([]))
        .finally(() => setLoadingTrending(false));
    } else {
      setFrequency("weekly");
      setContentLength("detailed");
      setLanguage("en");
      setShareUrl("");
      setTrendingTopics([]);
      setLoadingTrending(false);
    }
  }, [user, digest]);

  const handlePlayVoiceDigest = async () => {
    if (!user) {
      onShowToast("Please select a user profile to play Voice Digest.");
      return;
    }
    if (!digest) {
      onShowToast("No weekly digest compiled yet for this user.");
      return;
    }

    if (isPlayingVoice && audioRef.current) {
      audioRef.current.pause();
      setIsPlayingVoice(false);
      return;
    }

    if (audioRef.current && audioUrlRef.current) {
      audioRef.current
        .play()
        .then(() => setIsPlayingVoice(true))
        .catch((err: Error) => {
          onShowToast(`⚠️ Audio playback error: ${err.message}`);
        });
      return;
    }

    setLoadingVoice(true);
    try {
      const blob = await getDigestVoice(user.id);
      const url = URL.createObjectURL(blob);
      audioUrlRef.current = url;

      const audio = new Audio(url);
      audioRef.current = audio;

      audio.onended = () => {
        setIsPlayingVoice(false);
      };

      audio.onerror = () => {
        setIsPlayingVoice(false);
        onShowToast("⚠️ Failed to play audio stream.");
      };

      await audio.play();
      setIsPlayingVoice(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate Voice Digest.";
      onShowToast(`⚠️ ${msg}`);
      setIsPlayingVoice(false);
    } finally {
      setLoadingVoice(false);
    }
  };


  const handleCopyShareLink = async () => {
    if (!user || copyingShare) return;
    setCopyingShare(true);
    try {
      const res = await getOrCreateShareLink(user.id);
      const fullUrl = `${window.location.origin}/share/${res.share_token}`;
      setShareUrl(fullUrl);
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(fullUrl);
      } else {
        const textArea = document.createElement("textarea");
        textArea.value = fullUrl;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);
      }
      onShowToast("Share link copied to clipboard!");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate share link.";
      onShowToast(`⚠️ ${msg}`);
    } finally {
      setCopyingShare(false);
    }
  };


  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || savingPrefs) return;

    setSavingPrefs(true);
    setPrefError(null);
    try {
      const updatedUser = await updateUserPreferences(user.id, {
        digest_frequency: frequency,
        content_length: contentLength,
        digest_language: language,
      });
      if (onUserUpdated) {
        onUserUpdated(updatedUser);
      }
      onShowToast("Digest preferences saved successfully.");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save preferences.";
      setPrefError(msg);
    } finally {
      setSavingPrefs(false);
    }
  };

  useEffect(() => {
    if (!user) {
      setRecentActivities([]);
      return;
    }
    let isSubscribed = true;
    const fetchRecent = async () => {
      setLoadingActivity(true);
      try {
        const data = await getActivityLog(user.id, 5);
        if (isSubscribed) {
          setRecentActivities(data);
        }
      } catch {
        if (isSubscribed) {
          setRecentActivities([]);
        }
      } finally {
        if (isSubscribed) {
          setLoadingActivity(false);
        }
      }
    };

    fetchRecent();

    return () => {
      isSubscribed = false;
    };
  }, [user, digest]);

  return (
    <aside className="redesign-right-sidebar">
      {/* Panel 1: Your Digest is Ready */}
      <div className="right-panel-card ready-panel">
        <div className="right-panel-header">
          <span className="panel-header-icon">🎉</span>
          <h3 className="panel-header-title">Your Digest is Ready</h3>
        </div>
        <p className="panel-text-desc">
          {digest
            ? `Compiled for Week ${digest.week_identifier} with ${digest.items.length} top recommendations.`
            : "Select a user profile to load or compile their latest weekly digest."}
        </p>

        {/* Play Voice Digest */}
        <button
          type="button"
          className={
            loadingVoice
              ? "btn-voice-digest loading"
              : isPlayingVoice
              ? "btn-voice-digest playing"
              : "btn-voice-digest"
          }
          onClick={handlePlayVoiceDigest}
          disabled={!user || !digest || loadingVoice}
          title={
            !user
              ? "Select a user profile"
              : !digest
              ? "No digest available"
              : "Play Voice Digest Executive Summary"
          }
        >
          <span className="voice-play-icon">
            {loadingVoice ? "⏳" : isPlayingVoice ? "⏸" : "▶"}
          </span>
          <span>
            {loadingVoice
              ? "Generating Audio..."
              : isPlayingVoice
              ? "Pause Voice Digest"
              : "Play Voice Digest"}
          </span>
        </button>
      </div>

      {/* Panel 2: Your Interests */}
      <div className="right-panel-card interests-panel">
        <div className="right-panel-header">
          <div className="title-with-icon">
            <span className="panel-header-icon">🎯</span>
            <h3 className="panel-header-title">Your Interests</h3>
          </div>
          {user && (
            <button
              type="button"
              className="btn-edit-interests-link"
              onClick={onOpenEditInterests}
            >
              Edit ✏️
            </button>
          )}
        </div>

        {user && user.interest_tags && user.interest_tags.length > 0 ? (
          <div className="interests-pills-wrap">
            {user.interest_tags.map((tag) => (
              <span key={tag} className="interest-chip-pill">
                #{tag}
              </span>
            ))}
          </div>
        ) : (
          <p className="panel-empty-desc">No interest topics configured yet.</p>
        )}
      </div>

      {/* Panel 2.5: Trending in Your Topics */}
      <div className="right-panel-card trending-panel">
        <div className="right-panel-header">
          <span className="panel-header-icon">📈</span>
          <h3 className="panel-header-title">Trending in Your Topics</h3>
        </div>

        {loadingTrending ? (
          <p className="panel-empty-desc">Loading trends...</p>
        ) : trendingTopics.length > 0 ? (
          <div className="trending-topics-list">
            {trendingTopics.map((topic) => {
              const arrow =
                topic.direction === "up"
                  ? "↑"
                  : topic.direction === "down"
                  ? "↓"
                  : "→";
              const directionClass =
                topic.direction === "up"
                  ? "trend-up"
                  : topic.direction === "down"
                  ? "trend-down"
                  : "trend-flat";
              return (
                <div key={topic.category} className="trending-topic-row">
                  <div className="trending-topic-info">
                    <span className={`trending-arrow ${directionClass}`}>{arrow}</span>
                    <span className="trending-category-name">{topic.category}</span>
                  </div>
                  <span className="trending-count-badge">
                    {topic.current_count} {topic.current_count === 1 ? "story" : "stories"}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="panel-empty-desc">Not enough data yet — check back next week</p>
        )}
      </div>

      {/* Panel 3: Digest Preferences */}
      <div className="right-panel-card preferences-panel">
        <div className="right-panel-header">
          <span className="panel-header-icon">🎛️</span>
          <h3 className="panel-header-title">Digest Preferences</h3>
        </div>

        {prefError && (
          <div className="pref-error-text" style={{ fontSize: "0.75rem", color: "var(--error-color)", marginBottom: "0.5rem" }}>
            ⚠️ {prefError}
          </div>
        )}

        <form onSubmit={handleSavePreferences} className="pref-fields">
          <div className="pref-field-group">
            <label className="pref-label">Frequency</label>
            <select
              disabled={!user || savingPrefs}
              value={frequency}
              onChange={(e) => setFrequency(e.target.value)}
              className={user ? "pref-select" : "pref-select-disabled"}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly (Mondays)</option>
              <option value="monthly">Monthly (1st of month)</option>
            </select>
            <span className="pref-note-text">ℹ️ Affects future scheduled digests</span>
          </div>

          <div className="pref-field-group">
            <label className="pref-label">Content Length</label>
            <select
              disabled={!user || savingPrefs}
              value={contentLength}
              onChange={(e) => setContentLength(e.target.value)}
              className={user ? "pref-select" : "pref-select-disabled"}
            >
              <option value="brief">Brief (3 stories)</option>
              <option value="detailed">Detailed (5 stories)</option>
            </select>
          </div>

          <div className="pref-field-group">
            <label className="pref-label">Language</label>
            <select
              disabled={!user || savingPrefs}
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className={user ? "pref-select" : "pref-select-disabled"}
            >
              <option value="en">English (US)</option>
            </select>
          </div>

          {user && (
            <button
              type="submit"
              disabled={savingPrefs}
              className="btn-save-prefs"
            >
              {savingPrefs ? "Saving..." : "Save Preferences"}
            </button>
          )}
        </form>
      </div>

      {/* Panel 4: Share Your Digest */}
      <div className="right-panel-card share-panel">
        <div className="right-panel-header">
          <span className="panel-header-icon">🔗</span>
          <h3 className="panel-header-title">Share Your Digest</h3>
        </div>
        <p className="panel-text-desc">Generate a public read-only link for team sharing.</p>
        <div className="share-input-row">
          <input
            type="text"
            className={user ? "share-link-input" : "share-link-input-disabled"}
            value={
              shareUrl
                ? shareUrl
                : user
                ? "Click 'Copy Link' to generate URL"
                : "Select a user to generate link"
            }
            disabled={!user}
            readOnly
          />
          <button
            type="button"
            className={user ? "btn-copy-share" : "btn-copy-share-disabled"}
            disabled={!user || copyingShare}
            onClick={handleCopyShareLink}
          >
            {copyingShare ? "Copying..." : "Copy Link"}
          </button>
        </div>
      </div>

      {/* Panel 5: Recent Activity */}
      <div className="right-panel-card activity-panel">
        <div className="right-panel-header">
          <span className="panel-header-icon"><HistoryIcon /></span>
          <h3 className="panel-header-title">Recent Activity</h3>
        </div>

        {!user || recentActivities.length === 0 ? (
          <div className="activity-empty-state">
            <span className="activity-empty-icon">📋</span>
            <p className="activity-empty-title">
              {loadingActivity ? "Loading activity..." : "No recent activity recorded."}
            </p>
            <span className="activity-empty-sub">
              {loadingActivity ? "Fetching events" : "Actions you take will appear here"}
            </span>
          </div>
        ) : (
          <div className="sidebar-activity-list">
            {recentActivities.map((act) => {
              let icon: React.ReactNode = "📝";
              if (act.event_type === "digest_generated") icon = "✨";
              else if (act.event_type.includes("saved")) icon = <BookmarkIcon className="sidebar-act-icon-svg" />;
              else if (act.event_type.includes("feedback")) icon = "👍";
              else if (act.event_type.includes("interests")) icon = "🎯";

              return (
                <div key={act.id} className="sidebar-activity-item">
                  <span className="sidebar-act-icon">{icon}</span>
                  <div className="sidebar-act-details">
                    <span className="sidebar-act-desc">{act.description}</span>
                    <span className="sidebar-act-time">
                      {new Date(act.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </aside>
  );
};

