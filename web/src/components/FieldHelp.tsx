import { useEffect, useRef, useState } from "react";
import { t } from "../i18n";
import type { Locale, TranslationKey } from "../i18n";

interface Props {
  locale: Locale;
  label: TranslationKey;
  explanation: TranslationKey;
}

/** Pointer, keyboard and touch accessible contextual guidance. */
export function FieldHelp({ locale, label, explanation }: Props) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    if (!open) return;
    const closeOutside = (event: PointerEvent) => {
      if (event.target instanceof Node && !root.current?.contains(event.target))
        setOpen(false);
    };
    document.addEventListener("pointerdown", closeOutside);
    return () => document.removeEventListener("pointerdown", closeOutside);
  }, [open]);
  return (
    <span
      className="context-help"
      ref={root}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onKeyDown={(event) => {
        if (event.key === "Escape") setOpen(false);
      }}
    >
      <button
        type="button"
        className="context-help-trigger"
        aria-label={`${t(locale, "helpFor")}: ${t(locale, label)}`}
        aria-expanded={open}
        onFocus={() => setOpen(true)}
        onClick={() => setOpen((current) => !current)}
      >
        ?
      </button>
      {open && (
        <span className="context-help-popover" role="tooltip">
          {t(locale, explanation)}
        </span>
      )}
    </span>
  );
}
