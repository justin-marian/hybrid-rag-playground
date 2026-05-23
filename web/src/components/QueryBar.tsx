import { useEffect, useMemo, useState } from "react";

interface Props {
  initialQuery: string;
  loading: boolean;
  buttonLabel: string;
  onSubmit: (query: string) => void;
}

const PLACEHOLDER = "Ask a question, e.g. 'Does coffee raise cholesterol?'";


function SendIcon() {
  return (
    <svg
      className="querybar__btn-icon"
      viewBox="0 0 20 20"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M4 10H15M11 6L15 10L11 14"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function normalizeQuery(query: string): string {
  return query.trim();
}

export function QueryBar({ initialQuery, loading, buttonLabel, onSubmit }: Props) {
  const [text, setText] = useState(initialQuery);
  const query = useMemo(() => normalizeQuery(text), [text]);
  const canSubmit = !loading && query.length > 0;

  useEffect(() => {
    setText(initialQuery);
  }, [initialQuery]);

  function submit() {
    if (!canSubmit) {
      return;
    }

    onSubmit(query);
  }

  return (
    <div className="querybar-wrap">
      <section className="querybar">
        <textarea
          className="querybar__input"
          placeholder={PLACEHOLDER}
          rows={2}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
              event.preventDefault();
              submit();
            }
          }}
          aria-label="Query"
        />

        <button
          type="button"
          className="querybar__btn"
          onClick={submit}
          disabled={!canSubmit}
          aria-label={loading ? "Running query" : buttonLabel}
        >
          {loading ? (
            <span className="querybar__btn-loading loading-dots" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
          ) : (
            <>
              <span>{buttonLabel}</span>
              <SendIcon />
            </>
          )}
        </button>
      </section>
      <div className="querybar__hint">
        <kbd>⌘ Enter</kbd> / <kbd>Ctrl Enter</kbd>: Run query
      </div>
    </div>
  );
}
