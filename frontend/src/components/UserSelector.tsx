import React, { useEffect, useState } from "react";
import { getUsers } from "../api/client";
import { User } from "../types";

interface UserSelectorProps {
  selectedUserId: string | null;
  onUserSelect: (user: User) => void;
}

export const UserSelector: React.FC<UserSelectorProps> = ({
  selectedUserId,
  onUserSelect,
}) => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUserList = async () => {
    setLoading(true);
    setError(null);
    try {
      const userList = await getUsers();
      setUsers(userList);
      if (userList.length > 0 && !selectedUserId) {
        // Auto-select first user if none selected
        onUserSelect(userList[0]);
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Failed to load user list.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserList();
  }, []);

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const userId = e.target.value;
    const found = users.find((u) => u.id === userId);
    if (found) {
      onUserSelect(found);
    }
  };

  const selectedUser = users.find((u) => u.id === selectedUserId);

  if (loading) {
    return (
      <div className="user-selector-container skeleton-box">
        <span className="spinner-icon"></span>
        <span className="text-sm">Loading team members...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="user-selector-container selector-error-box">
        <span className="error-badge">Connection Error</span>
        <p className="error-text-sm">{error}</p>
        <button onClick={fetchUserList} className="btn-retry-sm">
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="user-selector-container">
      <div className="user-select-field">
        <label htmlFor="user-select" className="select-label">
          <svg
            className="label-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          Active User Profile
        </label>
        <div className="custom-select-wrapper">
          <select
            id="user-select"
            value={selectedUserId || ""}
            onChange={handleSelectChange}
            className="styled-select"
          >
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.name} ({user.id})
              </option>
            ))}
          </select>
          <span className="select-chevron">▼</span>
        </div>
      </div>

      {selectedUser && (
        <div className="user-interests-preview">
          <span className="interests-title">Tracked Topics:</span>
          <div className="tags-flex">
            {selectedUser.interest_tags.map((tag) => (
              <span key={tag} className="interest-pill">
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
