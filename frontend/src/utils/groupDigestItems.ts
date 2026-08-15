import { DigestItem } from "../types";

export interface DigestSection {
  id: string;
  title: string;
  items: DigestItem[];
}

/**
  * Groups an array of digest items into presentation sections:
  * 1. "Top Picks": Top 3 items by rank position.
  * 2. Open-Ended Sections: Remaining items grouped dynamically by their LLM-assigned section_title
  *    or primary category tag string.
  * 
  * Empty sections (zero items) are omitted.
  */
export function groupDigestItems(items: DigestItem[]): DigestSection[] {
  if (!items || items.length === 0) {
    return [];
  }

  // Sort items by rank_position ascending
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

  // Group remaining items dynamically by section_title, falling back to primary tag or "More For You"
  const dynamicSectionMap = new Map<string, DigestItem[]>();

  for (const item of remainingItems) {
    let sectionTitle = item.section_title?.trim ? item.section_title.trim() : item.section_title;
    if (!sectionTitle || sectionTitle.trim().length === 0) {
      if (item.category_tags && item.category_tags.length > 0 && item.category_tags[0].trim()) {
        sectionTitle = item.category_tags[0].trim();
      } else {
        sectionTitle = "More For You";
      }
    }

    sectionTitle = sectionTitle.trim();

    if (!dynamicSectionMap.has(sectionTitle)) {
      dynamicSectionMap.set(sectionTitle, []);
    }
    dynamicSectionMap.get(sectionTitle)!.push(item);
  }

  // Convert map to DigestSection array
  dynamicSectionMap.forEach((sectionItems, title) => {
    if (sectionItems.length > 0) {
      const slug = title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
      sections.push({
        id: `section-${slug || "more"}`,
        title,
        items: sectionItems,
      });
    }
  });

  return sections;
}
