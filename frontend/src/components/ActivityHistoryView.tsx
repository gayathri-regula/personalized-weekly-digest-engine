import React, { useEffect, useState } from "react";
import { getActivityLog } from "../api/client";
import { ActivityLogEntry, User } from "../types";
import { BookmarkIcon, HistoryIcon } from "./icons/NavIcons";

interface ActivityHistoryViewProps {
  user: User | null;
  onOpenDrawer: () => void;
}

const getEventIcon = (eventType: string): React.ReactNode => {
  switch (eventType) {
    case "digest_generated":
      return "✨";
    case "item_saved":
    case "item_unsaved":
      return <BookmarkIcon className="timeline-icon-svg" />;
    case "feedback_submitted":
      return "👍";
    case "interests_updated":
      return "🎯";
    default:
      return "📝";
  }
};

const formatTimestamp = (isoString: string): string => {
  try {
    const date = new Date(isoString);
    return date.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
};

export const ActivityHistoryView: React.FC<ActivityHistoryViewProps> = ({
  user,
  onOpenDrawer,
}) => {
  const [activities, setActivities] = useState<ActivityLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    if (!user) {
      setActivities([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getActivityLog(user.id, 50);
      setActivities(data);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to load activity history.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [user]);

  if (!user) {
    return (
      <div className="activity-history-empty-container">
        <div className="placeholder-icon">👤</div>
        <h3>No User Profile Selected</h3>
        <p>Please select a user profile to view their activity log history.</p>
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
      <div className="activity-history-view">
        <div className="activity-history-header">
          <div className="activity-title-group">
            <span className="activity-header-icon"><HistoryIcon /></span>
            <h2 className="activity-main-heading">Activity History</h2>
            <span className="activity-count-badge">Loading...</span>
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
      <div className="activity-history-view">
        <div className="digest-error-card">
          <div className="error-card-header">
            <span className="error-badge-lg">Server Error</span>
            <h3>Couldn't fetch activity history</h3>
          </div>
          <p>{error}</p>
          <button onClick={fetchHistory} className="btn-retry-lg">
            Try Reloading
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="activity-history-view">
      <div className="activity-history-header">
        <div className="activity-title-group">
          <span className="activity-header-icon"><HistoryIcon /></span>
          <h2 className="activity-main-heading">Activity History</h2>
          <span className="activity-count-badge">
            {activities.length} {activities.length === 1 ? "Event" : "Events"}
          </span>
        </div>
      </div>

      {activities.length === 0 ? (
        <div className="activity-empty-box">
          <span className="activity-empty-large-icon">📋</span>
          <h3>No activity history recorded yet</h3>
          <p>
            Actions like generating weekly digests, saving stories, updating interest topics, and leaving feedback will appear here.
          </p>
        </div>
      ) : (
        <div className="activity-timeline-list">
          {activities.map((item) => (
            <div key={item.id} className="activity-timeline-item">
              <div className="activity-icon-badge">
                {getEventIcon(item.event_type)}
              </div>
              <div className="activity-item-content">
                <div className="activity-item-main">
                  <p className="activity-description-text">{item.description}</p>
                  <span className="activity-type-chip">{item.event_type}</span>
                </div>
                <span className="activity-time-stamp">
                  {formatTimestamp(item.created_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
