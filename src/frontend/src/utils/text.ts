export function containerStatusBadge(
  status: string
): "success" | "processing" | "warning" | "error" | "default" {
  switch (status) {
    case "running":
      return "processing";
    case "created":
      return "default";
    case "paused":
    case "restarting":
      return "warning";
    case "exited":
      return "default";
    case "dead":
    case "removing":
      return "error";
    default:
      return "default";
  }
}

export function shortId(id: string | null | undefined, len = 12): string {
  if (!id) return "";
  const stripped = id.replace(/^sha256:/, "");
  return stripped.length > len ? stripped.slice(0, len) : stripped;
}

export function imageDisplayName(image: { id: string; tags: string[] } | null | undefined): string {
  if (!image) return "";
  if (image.tags && image.tags.length > 0) return image.tags.join(", ");
  return shortId(image.id);
}
