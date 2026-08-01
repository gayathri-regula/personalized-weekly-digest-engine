import React, { useState } from "react";
import { DigestView } from "./components/DigestView";
import { SideDrawer } from "./components/SideDrawer";
import { User } from "./types";
import "./App.css";

export const App: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [userRefreshKey, setUserRefreshKey] = useState<number>(0);

  const handleUserSelect = (user: User) => {
    setSelectedUser(user);
  };

  const handleUserCreated = (newUser: User) => {
    setUserRefreshKey((prev) => prev + 1);
    setSelectedUser(newUser);
  };

  return (
    <div className="app-layout">
      {/* Top Navbar */}
      <header className="app-navbar">
        <div className="navbar-container">
          <div className="navbar-left">
            <button
              onClick={() => setIsDrawerOpen(true)}
              className="hamburger-btn"
              aria-label="Open profile controls drawer"
            >
              ☰
            </button>
            <div className="brand-logo">
              <span className="logo-icon">⚡</span>
              <div className="brand-text">
                <span className="brand-name">Personalized Digest Engine</span>
                <span className="brand-sub">
                  AI Relevance Ranker & Prose Summarizer
                </span>
              </div>
            </div>
          </div>
          <div className="navbar-badge">
            <span className="status-dot"></span>
            Live Supabase Postgres
          </div>
        </div>
      </header>

      {/* Side Drawer Component */}
      <SideDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        selectedUser={selectedUser}
        onUserSelect={handleUserSelect}
        onUserCreated={handleUserCreated}
        refreshKey={userRefreshKey}
      />

      {/* Main Content Body */}
      <main className="app-main-content">
        <div className="content-container">
          {/* Main Digest View Section */}
          <section className="digest-display-area">
            <DigestView user={selectedUser} />
          </section>
        </div>
      </main>

      {/* App Footer */}
      <footer className="app-footer">
        <p>Personalized Weekly Digest Engine • React Frontend</p>
      </footer>
    </div>
  );
};

export default App;
