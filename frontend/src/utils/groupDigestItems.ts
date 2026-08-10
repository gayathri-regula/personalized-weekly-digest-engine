import { DigestItem } from "../types";

export interface DigestSection {
  id: string;
  title: string;
  items: DigestItem[];
}

/**
 * Human-readable section label mapping for the 12-tag taxonomy.
 */
export const TAG_TO_SECTION_MAP: Record<string, string> = {
  "AI": "AI & Machine Learning",
  "Machine Learning": "AI & Machine Learning",
  "Python": "Languages & Ecosystems",
  "JavaScript": "Languages & Ecosystems",
  "Cloud": "Cloud & DevOps",
  "DevOps": "Cloud & DevOps",
  "Data Science": "Data Science & Analytics",
  "Mobile Development": "Frontend & Mobile",
  "UI/UX Design": "Frontend & Mobile",
  "Backend Engineering": "Backend Engineering",
  "Security": "Security & Infrastructure",
  "Open Source": "Open Source & Community",
};

/**
 * Groups an array of digest items into presentation sections:
 * 1. "Top Picks": Top 3 items by relevance score / rank position.
 * 2. Tag-based sections: Remaining items grouped by their primary category tag,
 *    mapped to human-readable section labels.
 * 
 * Empty sections (zero items) are omitted.
 */
export function groupDigestItems(items: DigestItem[]): DigestSection[] {
  if (!items || items.length === 0) {
    return [];
  }

  // Sort items by rank_position ascending (or relevance_score descending)
  const sortedItems = [...items].sort((a, b) => a.rank_position - b.rank_position);

  // Top 3 items go into Top Picks
  const topPicks = sortedItems.slice(0, 3);
  const remainingItems = sortedItems.slice(3);

  const sections: DigestSection[] = [];

  if (topPicks.length > 0) {
    sections.push({
      id: "top-picks",
      title: "Top Picks",
      items: topPicks,
    });
  }

  // Group remaining items by mapped section title
  const tagSectionMap = new Map<string, DigestItem[]>();

  for (const item of remainingItems) {
    const primaryTag =
      item.category_tags && item.category_tags.length > 0
        ? item.category_tags[0]
        : "Other";

    const sectionTitle = TAG_TO_SECTION_MAP[primaryTag] || primaryTag;

    if (!tagSectionMap.has(sectionTitle)) {
      tagSectionMap.set(sectionTitle, []);
    }
    tagSectionMap.get(sectionTitle)!.push(item);
  }

  // Convert map to DigestSection array
  tagSectionMap.forEach((sectionItems, title) => {
    if (sectionItems.length > 0) {
      const slug = title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
      sections.push({
        id: `section-${slug}`,
        title,
        items: sectionItems,
      });
    }
  });

  return sections;
}
