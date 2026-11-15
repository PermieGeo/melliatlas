import { useCallback, useEffect, useRef, useState } from "react";
import { getInvestigation, startInvestigation } from "../api/client";
import type { Investigation, InvestigationCreate } from "../api/types";
import { failure, investigationNotice } from "../notifications";
import type { Notice } from "../notifications";

const MAX_POLLS = 24;
const POLL_INTERVAL_MS = 700;

/** Abortable delay that also settles when a country switch cancels the workflow. */
async function pause(
  milliseconds: number,
  signal: AbortSignal,
): Promise<boolean> {
  if (signal.aborted) return false;
  return new Promise((resolve) => {
    const handle = setTimeout(() => finish(true), milliseconds);
    const onAbort = () => finish(false);
    function finish(completed: boolean) {
      clearTimeout(handle);
      signal.removeEventListener("abort", onAbort);
      resolve(completed);
    }
    signal.addEventListener("abort", onAbort, { once: true });
  });
}

/** Owns request identity, cancellation and bounded polling; views never start HTTP work. */
export function useInvestigation() {
  const [result, setResult] = useState<Investigation | null>(null);
  const [selectedSite, setSelectedSite] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [busy, setBusy] = useState(false);
  const activeRequest = useRef<AbortController | null>(null);
  const sequence = useRef(0);

  const cancel = useCallback(() => {
    sequence.current += 1;
    activeRequest.current?.abort();
    activeRequest.current = null;
  }, []);

  const reset = useCallback(() => {
    cancel();
    setBusy(false);
    setResult(null);
    setSelectedSite(null);
    setNotice(null);
  }, [cancel]);

  useEffect(() => () => cancel(), [cancel]);

  const begin = useCallback(
    async (request: InvestigationCreate | string) => {
      reset();
      const identity = sequence.current;
      const controller = new AbortController();
      activeRequest.current = controller;
      setBusy(true);
      const response =
        typeof request === "string"
          ? await getInvestigation(request, controller.signal)
          : await startInvestigation(request, controller.signal);
      if (controller.signal.aborted || sequence.current !== identity) return;
      if (response.kind === "error") {
        activeRequest.current = null;
        setNotice(failure(response));
        setBusy(false);
        return;
      }
      let snapshot = response.data;
      setResult(snapshot);
      for (
        let attempt = 0;
        attempt < MAX_POLLS &&
        (snapshot.status === "QUEUED" || snapshot.status === "RUNNING");
        attempt++
      ) {
        if (!(await pause(POLL_INTERVAL_MS, controller.signal))) return;
        const updated = await getInvestigation(snapshot.id, controller.signal);
        if (controller.signal.aborted || sequence.current !== identity) return;
        if (updated.kind === "error") {
          activeRequest.current = null;
          setNotice(failure(updated));
          setBusy(false);
          return;
        }
        snapshot = updated.data;
        setResult(snapshot);
      }
      if (controller.signal.aborted || sequence.current !== identity) return;
      activeRequest.current = null;
      setBusy(false);
      setSelectedSite(snapshot.plan?.stops[0]?.site_id ?? null);
      setNotice(investigationNotice(snapshot));
    },
    [reset],
  );

  return { result, selectedSite, setSelectedSite, notice, busy, begin, reset };
}
