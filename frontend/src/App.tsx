import React, { useState } from "react";
import { DigestView } from "./components/DigestView";
import { UserSelector } from "./components/UserSelector";
import { User } from "./types";
import "./App.css";

export const App: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  const handleUserSelect = (user: User) => {
    setSelectedUser(user);
  };

  return (
    <div className="app-layout">
      {/* Top Navbar */}
      <header className="app-navbar">
        <div className="navbar-container">
          <div className="brand-logo">
            <span className="logo-icon">⚡</span>
            <div className="brand-text">
              <span className="brand-name">Personalized Digest Engine</span>
              <span className="brand-sub">AI Relevance Ranker & Prose Summarizer</span>
            </div>
          </div>
          <div className="navbar-badge">
            <span className="status-dot"></span>
            Live Supabase Postgres
          </div>
        </div>
      </header>

      {/* Main Content Body */}
      <main className="app-main-content">
        <div className="content-container">
          {/* User Selection Controls Bar */}
          <section className="user-selection-bar">
            <UserSelector
              selectedUserId={selectedUser?.id || null}
              onUserSelect={handleUserSelect}
            />
          </section>

          {/* Digest View Section */}
          <section className="digest-display-area">
            <DigestView user={selectedUser} />
          </section>
        </div>
      </main>

      {/* App Footer */}
      <footer className="app-footer">
        <p>Personalized Weekly Digest Engine • Phase 9 React Frontend</p>
      </footer>
    </div>
  );
};

export default App;
