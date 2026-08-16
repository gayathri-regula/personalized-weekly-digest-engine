/**
 * Helper utility to return appropriate category icons and light-themed gradient backgrounds
 * for story thumbnail badges and category highlight cards.
 * 
 * Uses exact word-boundary matching to prevent substring false-positives (e.g. "ai" inside "Container Orchestration").
 */

export interface CategoryTheme {
  icon: string;
  gradient: string;
  borderColor: string;
}

const CATEGORY_THEMES: Record<string, CategoryTheme> = {
  "top-picks": {
    icon: "⭐",
    gradient: "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
    borderColor: "#f59e0b",
  },
  ai: {
    icon: "🤖",
    gradient: "linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)",
    borderColor: "#6366f1",
  },
  machine: {
    icon: "🧠",
    gradient: "linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)",
    borderColor: "#8b5cf6",
  },
  cloud: {
    icon: "☁️",
    gradient: "linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%)",
    borderColor: "#0ea5e9",
  },
  security: {
    icon: "🔒",
    gradient: "linear-gradient(135deg, #fee2e2 0%, #fca5a5 100%)",
    borderColor: "#ef4444",
  },
  devops: {
    icon: "⚙️",
    gradient: "linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)",
    borderColor: "#10b981",
  },
  data: {
    icon: "📊",
    gradient: "linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%)",
    borderColor: "#ec4899",
  },
  web: {
    icon: "🌐",
    gradient: "linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)",
    borderColor: "#3b82f6",
  },
  mobile: {
    icon: "📱",
    gradient: "linear-gradient(135deg, #ccfbf1 0%, #99f6e4 100%)",
    borderColor: "#14b8a6",
  },
  architecture: {
    icon: "🏗️",
    gradient: "linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%)",
    borderColor: "#f97316",
  },
};

export function getCategoryTheme(categoryStr?: string): CategoryTheme {
  if (!categoryStr) {
    return {
      icon: "📰",
      gradient: "linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%)",
      borderColor: "#94a3b8",
    };
  }

  // Tokenize the input category string into lowercased words
  const inputWords = new Set(
    categoryStr
      .toLowerCase()
      .split(/[^a-z0-9]+/g)
      .filter((w) => w.length > 0)
  );

  for (const [key, theme] of Object.entries(CATEGORY_THEMES)) {
    const keyWords = key
      .toLowerCase()
      .split(/[^a-z0-9]+/g)
      .filter((w) => w.length > 0);

    // Check if every word of the theme key is present in the input category's tokenized words
    if (
      keyWords.length > 0 &&
      keyWords.every((kw) => inputWords.has(kw))
    ) {
      return theme;
    }
  }

  // Default fallback theme for unrecognized or custom open-ended categories
  return {
    icon: "⚡",
    gradient: "linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)",
    borderColor: "#4f46e5",
  };
}
