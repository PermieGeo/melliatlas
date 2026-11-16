import type { ApiResult } from "./api/client";
import type { Investigation } from "./api/types";
import type { TranslationKey } from "./i18n";

/** Renderable notices contain translation keys, not language-specific text. */
export interface Notice {
  kind: "error" | "info";
  key: TranslationKey;
  values?: Record<string, string | number>;
}

/** Standard HTTP statuses are protocol values, not a configurable domain enum. */
const statusMessageKeys: Readonly<Record<number, TranslationKey>> = {
  404: "errorMissing",
  409: "errorDepth",
  422: "errorInvalid",
  503: "errorUnavailable",
};

/** Map stable HTTP failures to localized notices; never render raw provider text. */
export function failure<T>(
  result: Extract<ApiResult<T>, { kind: "error" }>,
): Notice {
  if (result.code === "ABORTED") return { kind: "info", key: "errorAborted" };
  const key =
    result.status === null ? undefined : statusMessageKeys[result.status];
  return key
    ? { kind: "error", key }
    : { kind: "error", key: "errorOther", values: { code: result.code } };
}

/** Technical completion and domain feasibility are separate lifecycle outcomes. */
export function investigationNotice(result: Investigation): Notice | null {
  if (result.status === "QUEUED" || result.status === "RUNNING")
    return { kind: "info", key: "pending" };
  if (result.status === "FAILED") return { kind: "error", key: "failed" };
  if (!result.plan) return { kind: "info", key: "insufficient" };
  return null;
}
