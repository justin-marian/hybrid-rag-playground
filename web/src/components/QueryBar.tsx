import { useEffect, useMemo, useState } from "react";

interface Props {
  initialQuery: string;
  loading: boolean;
  buttonLabel: string;
  onSubmit: (query: string) => void;
}

const PLACEHOLDER = "Ask a question, e.g. 'Does coffee raise cholesterol?'";

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
      />

      <button
        type="button"
        className="querybar__btn"
        onClick={submit}
        disabled={!canSubmit}
      >
        {loading ? "…" : buttonLabel}
      </button>
    </section>
  );
}
