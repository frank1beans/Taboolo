export function shortenDescription(text: string | null | undefined, keep = 50): string {
  const trimmed = (text ?? "").trim();
  if (!trimmed) {
    return "";
  }
  if (trimmed.length <= keep * 2 + 5) {
    return trimmed;
  }
  const start = trimmed.slice(0, keep).trimEnd();
  const end = trimmed.slice(-keep).trimStart();
  return `${start}\n...\n${end}`;
}
