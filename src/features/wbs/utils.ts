import type {
  ApiWbs6Node,
  ApiWbs7Node,
  ApiWbsSpazialeNode,
  ApiWbsVisibilityEntry,
} from "@/types/api";

import { WBS_LEVELS, WBS_LEVEL_TITLES } from "./constants";
import type { VisibilitySection } from "./types";

const buildVisibilityMap = (entries: ApiWbsVisibilityEntry[]) => {
  const map = new Map<string, boolean>();
  entries.forEach((entry) => {
    map.set(`${entry.level}:${entry.node_id}`, entry.hidden);
  });
  return map;
};

const normalizeNode = (
  level: number,
  nodeId: number,
  code: string | null | undefined,
  description: string | null | undefined,
  visibilityMap: Map<string, boolean>,
) => ({
  id: nodeId,
  code: code?.trim() ?? "",
  description: description ?? "",
  hidden: visibilityMap.get(`${level}:${nodeId}`) ?? false,
});

export function buildVisibilitySections(params: {
  spaziali: ApiWbsSpazialeNode[];
  wbs6: ApiWbs6Node[];
  wbs7: ApiWbs7Node[];
  visibility: ApiWbsVisibilityEntry[];
}): VisibilitySection[] {
  const { spaziali, wbs6, wbs7, visibility } = params;
  const visibilityMap = buildVisibilityMap(visibility);

  return WBS_LEVELS.map((level) => {
    let nodes = [];
    if (level >= 1 && level <= 5) {
      nodes = spaziali
        .filter((node) => node.level === level)
        .map((node) =>
          normalizeNode(level, node.id, node.code, node.description, visibilityMap),
        );
    } else if (level === 6) {
      nodes = wbs6.map((node) =>
        normalizeNode(level, node.id, node.code, node.description, visibilityMap),
      );
    } else {
      nodes = wbs7.map((node) =>
        normalizeNode(level, node.id, node.code, node.description, visibilityMap),
      );
    }

    nodes.sort((a, b) => {
      const codeCompare = a.code.localeCompare(b.code, "it-IT");
      if (codeCompare !== 0) return codeCompare;
      return (a.description ?? "").localeCompare(b.description ?? "", "it-IT");
    });

    return {
      level,
      title: WBS_LEVEL_TITLES[level],
      nodes,
    };
  }).filter((section) => section.nodes.length > 0);
}
