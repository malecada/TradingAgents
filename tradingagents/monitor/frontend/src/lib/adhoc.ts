export function isTerminal(status: string | undefined): boolean {
  return status === "done" || status === "error";
}

/** React Query refetchInterval: poll every 2s until the run is terminal. */
export function pollInterval(status: string | undefined): number | false {
  return isTerminal(status) ? false : 2000;
}
