export interface VisibilityNode {
  id: number;
  code: string;
  description: string | null;
  hidden: boolean;
}

export interface VisibilitySection {
  level: number;
  title: string;
  nodes: VisibilityNode[];
}
