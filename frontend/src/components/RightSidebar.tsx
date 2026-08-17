import React, { useEffect, useState } from "react";
import { getActivityLog } from "../api/client";
import { ActivityLogEntry, Digest, User } from "../types";

interface RightSidebarProps {
  user: User | null;
  digest: Digest | null;
  onOpenEditInterests: () => void;
  onShowToast: (message: string) => void;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({
  user,
  digest,
  onOpenEditInterests,
  onShowToast,
}) => {
  const [recentActivities, setRecentActivities] = useState<ActivityLogEntry[]>([]);
  const [loadingActivity, setLoadingActivity] = useState<boolean>(false);

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

        {/* Play Voice Digest (Visual Placeholder) */}
        <button
          type="button"
          className="btn-voice-digest-placeholder"
          onClick={() =>
            onShowToast("This feature is scheduled for a future update.")
          }
          title="Play Voice Digest (Coming Soon)"
        >
          <span className="voice-play-icon">▶</span>
          <span>Play Voice Digest</span>
          <span className="redesign-soon-badge">Soon</span>
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

      {/* Panel 3: Digest Preferences (Visual Placeholder) */}
      <div className="right-panel-card preferences-panel">
        <div className="right-panel-header">
          <span className="panel-header-icon">🎛️</span>
          <h3 className="panel-header-title">Digest Preferences</h3>
          <span className="redesign-soon-badge">Soon</span>
        </div>
        <div className="pref-fields-disabled">
          <div className="pref-field-group">
            <label className="pref-label">Frequency</label>
            <select disabled value="weekly" className="pref-select-disabled">
              <option value="weekly">Weekly (Mondays)</option>
            </select>
          </div>
          <div className="pref-field-group">
            <label className="pref-label">Content Length</label>
            <select disabled value="medium" className="pref-select-disabled">
              <option value="medium">Detailed Digest</option>
            </select>
          </div>
          <div className="pref-field-group">
            <label className="pref-label">Language</label>
            <select disabled value="en" className="pref-select-disabled">
              <option value="en">English (US)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Panel 4: Share Your Digest (Visual Placeholder) */}
      <div className="right-panel-card share-panel">
        <div className="right-panel-header">
          <span className="panel-header-icon">🔗</span>
          <h3 className="panel-header-title">Share Your Digest</h3>
        </div>
        <p className="panel-text-desc">Generate a public read-only link for team sharing.</p>
        <div className="share-input-row">
          <input
            type="text"
            className="share-link-input-disabled"
            value="https://digest.sfcollab.internal/d/preview"
            disabled
            readOnly
          />
          <button
            type="button"
            className="btn-copy-share-disabled"
            onClick={() =>
              onShowToast("This feature is scheduled for a future update.")
            }
          >
            Copy Link
          </button>
        </div>
      </div>

      {/* Panel 5: Recent Activity */}
      <div className="right-panel-card activity-panel">
        <div className="right-panel-header">
          <span className="panel-header-icon">🕒</span>
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
              let icon = "📝";
              if (act.event_type === "digest_generated") icon = "✨";
              else if (act.event_type.includes("saved")) icon = "🔖";
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

