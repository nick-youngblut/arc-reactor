export const formatDuration = (durationMs?: number | null): string => {
  if (!durationMs || durationMs <= 0) return '—';
  const totalSeconds = Math.floor(durationMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours) {
    return `${hours}h ${minutes % 60}m`;
  }
  if (minutes) {
    return `${minutes}m`;
  }
  return `${totalSeconds}s`;
};
