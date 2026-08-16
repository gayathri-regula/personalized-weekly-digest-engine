import React from "react";
import { Digest, User } from "../types";
import { GenerateButton } from "./GenerateButton";

interface HeroDigestCardProps {
  user: User;
  digest: Digest;
  onSuccess: (newDigest: Digest) => void;
}

export const HeroDigestCard: React.FC<HeroDigestCardProps> = ({
  user,
  digest,
  onSuccess,
}) => {
  const formattedDate = new Date(digest.generated_at).toLocaleDateString(
    undefined,
    {
      weekday: "long",
      year: "numeric",
      month: "short",
      day: "numeric",
    }
  );

  const totalStories = digest.items.length;
  const distinctTopics = new Set(
    digest.items.map((i) => i.section_title || i.category_tags[0] || "General")
  ).size;

  return (
    <section className="redesign-hero-card">
      {/* Top Meta Row */}
      <div className="hero-meta-row">
        <div className="hero-badge-group">
          <span className="hero-week-chip">Week {digest.week_identifier}</span>
          <span className="hero-status-dot">● Published</span>
          <span className="hero-date-str">Compiled {formattedDate}</span>
        </div>

        <GenerateButton
          userId={user.id}
          onSuccess={onSuccess}
          label="Regenerate Digest"
          variant="secondary"
        />
      </div>

      {/* Hero Title Header */}
      <div className="hero-header-text">
        <h2 className="hero-main-title">Weekly Digest</h2>
        <p className="hero-main-sub">
          AI-curated recommendations and executive highlights for{" "}
          <strong>{user.name}</strong> based on {user.interest_tags.length} followed topics.
        </p>
      </div>

      {/* Metrics Row */}
      <div className="hero-metrics-grid">
        <div className="hero-metric-tile">
          <span className="metric-tile-icon">📰</span>
          <div className="metric-tile-body">
            <span className="metric-tile-value">{totalStories} Stories</span>
            <span className="metric-tile-label">Ranked Highlights</span>
          </div>
        </div>

        <div className="hero-metric-tile">
          <span className="metric-tile-icon">🏷️</span>
          <div className="metric-tile-body">
            <span className="metric-tile-value">{distinctTopics} Categories</span>
            <span className="metric-tile-label">Covered Topics</span>
          </div>
        </div>

        <div className="hero-metric-tile">
          <span className="metric-tile-icon">🎯</span>
          <div className="metric-tile-body">
            <span className="metric-tile-value">
              {user.interest_tags.length} Interests
            </span>
            <span className="metric-tile-label">Active Focus</span>
          </div>
        </div>
      </div>

      {/* Executive Summary Prose Block */}
      {digest.summary_prose && (
        <div className="hero-prose-container">
          <div className="prose-header-row">
            <span className="prose-sparkle-icon">✨</span>
            <h3 className="prose-section-heading">Executive Summary</h3>
          </div>
          <div className="prose-rendered-body">
            {renderMarkdownProse(digest.summary_prose)}
          </div>
        </div>
      )}
    </section>
  );
};

/**
 * Reused inline markdown rendering logic for prose summary.
 */
function renderMarkdownProse(prose: string) {
  if (!prose) return null;

  const lines = prose.split("\n");
  const elements: React.ReactNode[] = [];
  let inList = false;
  let listItems: React.ReactNode[] = [];

  lines.forEach((line, idx) => {
    const trimmed = line.trim();
    if (!trimmed) {
      if (inList) {
        elements.push(
          <ul key={`ul-${idx}`} className="prose-list-ul">
            {listItems}
          </ul>
        );
        inList = false;
        listItems = [];
      }
      return;
    }

    if (trimmed.startsWith("### ")) {
      if (inList) {
        elements.push(
          <ul key={`ul-${idx}`} className="prose-list-ul">
            {listItems}
          </ul>
        );
        inList = false;
        listItems = [];
      }
      elements.push(
        <h4 key={idx} className="prose-h4-sub">
          {parseInlineFormatting(trimmed.substring(4))}
        </h4>
      );
    } else if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      inList = true;
      listItems.push(
        <li key={idx} className="prose-list-li">
          {parseInlineFormatting(trimmed.substring(2))}
        </li>
      );
    } else {
      if (inList) {
        elements.push(
          <ul key={`ul-${idx}`} className="prose-list-ul">
            {listItems}
          </ul>
        );
        inList = false;
        listItems = [];
      }
      elements.push(
        <p key={idx} className="prose-p-block">
          {parseInlineFormatting(trimmed)}
        </p>
      );
    }
  });

  if (inList) {
    elements.push(
      <ul key="ul-final" className="prose-list-ul">
        {listItems}
      </ul>
    );
  }

  return <div className="prose-wrapper">{elements}</div>;
}

function parseInlineFormatting(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*|`.*?`)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={index}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}
