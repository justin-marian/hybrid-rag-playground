import { useEffect, useState } from "react";

import {
  api,
  type DatasetInfo,
  type RetrieveResponse,
  type RagResponse,
  type RetrieverName,
} from "./api";
import { Controls, type ControlsState } from "./components/Controls";
import { Header } from "./components/Header";
import { HitsList } from "./components/HitsList";
import { QueryBar } from "./components/QueryBar";
import { RagAnswerPanel } from "./components/RagAnswerPanel";

const DEFAULT_STATE: ControlsState = {
  dataset: "scifact",
  retriever: "hybrid",
  topK: 5,
  alpha: 0.5,
  mode: "retrieve",
};

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="banner banner--error" role="alert">
      <svg
        className="banner__icon"
        viewBox="0 0 20 20"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <path
          d="M10 6.5V10.5M10 13.5H10.005M2.5 16.5H17.5L10 3.5L2.5 16.5Z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span>{message}</span>
    </div>
  );
}

function LoadingPanel({ label }: { label: string }) {
  return (
    <div className="loading" role="status" aria-live="polite">
      <span className="loading__spinner" aria-hidden="true" />
      <span className="loading__text">{label}</span>
    </div>
  );
}

export default function App() {
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [controls, setControls] = useState<ControlsState>(DEFAULT_STATE);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retrieval, setRetrieval] = useState<RetrieveResponse | null>(null);
  const [rag, setRag] = useState<RagResponse | null>(null);

  // Bootstrap datasets on mount
  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const list = await api.datasets();
        const safeList = Array.isArray(list) ? list : [];
        if (cancelled) return;

        setDatasets(safeList);
        setControls((prev) => {
          const exists = safeList.some((dataset) => dataset.key === prev.dataset);

          return {
            ...prev,
            dataset: exists ? prev.dataset : safeList[0]?.key ?? ""
          };
        });
      } catch (err) {
        if (cancelled) return;
        setError((err as Error).message);
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(q: string) {
    setQuery(q);
    setLoading(true);
    setError(null);
    setRetrieval(null);
    setRag(null);

    if (!controls.dataset) {
      setLoading(false);
      setError("No dataset is selected. Wait for datasets to load, then try again.");
      return;
    }

    try {
      if (controls.mode === "retrieve") {
        const res = await api.retrieve({
          dataset: controls.dataset,
          query: q,
          retriever: controls.retriever as RetrieverName,
          top_k: controls.topK,
          alpha: controls.retriever === "hybrid" ? controls.alpha : null,
        });
        setRetrieval(res);
      } else {
        const res = await api.rag({
          dataset: controls.dataset,
          query: q,
          retriever: controls.retriever as RetrieverName,
          top_k: controls.topK,
          alpha: controls.retriever === "hybrid" ? controls.alpha : null,
        });
        setRag(res);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  const buttonLabel = controls.mode === "generate" ? "Generate" : "Retrieve";
  const loadingLabel = controls.mode === "generate" ? "Generating answer. This may take a moment with local Ollama models…" : "Retrieving top chunks…";

  return (
    <div className="page">
      <Header />

      <Controls
        datasets={datasets}
        state={controls}
        onChange={setControls}
        disabled={loading}
      />

      <QueryBar
        initialQuery={query}
        loading={loading}
        buttonLabel={buttonLabel}
        onSubmit={handleSubmit}
      />

      {error && <ErrorBanner message={error} />}
      {loading && <LoadingPanel label={loadingLabel} />}

      {retrieval && !loading && (
        <section className="results">
          <div className="results__meta">
            <span>
              retriever: <code>{retrieval.retriever}</code>
            </span>
            {retrieval.alpha !== null && (
              <span>
                alpha: <code>{retrieval.alpha.toFixed(2)}</code>
              </span>
            )}
            <span>
              top-k: <code>{retrieval.top_k}</code>
            </span>
            <span>
              hits: <code>{retrieval.hits.length}</code>
            </span>
          </div>
          <HitsList hits={retrieval.hits} />
        </section>
      )}

      {rag && !loading && <RagAnswerPanel response={rag} />}

      <footer className="footer">
        <span className="footer__left">
          Hybrid RAG · Local AI Search
        </span>
        <span className="footer__right">
          <span className="footer__hint">
            <kbd>⌘ Enter</kbd> / <kbd>Ctrl Enter</kbd>: Run query
          </span>
          <a href="http://localhost:5173/docs" target="_blank" rel="noreferrer">
            API docs ↗
          </a>
        </span>
      </footer>
    </div>
  );
}
