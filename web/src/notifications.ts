import type { ApiResult } from "./api/client";
import type { Investigation } from "./api/types";
import type { TranslationKey } from "./i18n";

/** Renderable notices contain translation keys, not language-specific text. */
export interface Notice {
  kind: "error" | "info";
  key: TranslationKey;
  values?: Record<string, string | number>;
}

/** Map typed API failures into user-facing states without trusting server text as UI copy. */
export function failure<T>(
  result: Extract<ApiResult<T>, { kind: "error" }>,
): Notice {
  if (result.code === "ABORTED") return { kind: "info", key: "errorAborted" };
  if (result.status === 404) return { kind: "error", key: "errorMissing" };
  if (result.status === 422) return { kind: "error", key: "errorInvalid" };
  if (result.status === 409) return { kind: "error", key: "errorDepth" };
  if (result.status === 503) return { kind: "error", key: "errorUnavailable" };
  return { kind: "error", key: "errorOther", values: { code: result.code } };
}

/** Technical completion and domain feasibility are separate lifecycle outcomes. */
export function investigationNotice(result: Investigation): Notice | null {
  if (result.status === "QUEUED" || result.status === "RUNNING")
    return { kind: "info", key: "pending" };
  if (result.status === "FAILED") return { kind: "error", key: "failed" };
  if (!result.plan) return { kind: "info", key: "insufficient" };
  return null;
}
