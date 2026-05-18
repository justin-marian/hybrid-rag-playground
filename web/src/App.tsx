import { useCallback, useEffect, useState } from "react";

import {
  api,
  type DatasetInfo,
  type RagRequest,
  type RagResponse,
  type RetrieveRequest,
  type RetrieveResponse
} from "./api";
import { Controls, type ControlsState } from "./components/Controls";
import { Header } from "./components/Header";
import { HitsList } from "./components/HitsList";
import { QueryBar } from "./components/QueryBar";
import { RagAnswerPanel } from "./components/RagAnswerPanel";

const DEFAULT_CONTROLS: ControlsState = {
  dataset: "scifact",
  retriever: "hybrid",
  topK: 5,
  alpha: 0.5,
  mode: "rag"
};

function alphaValue(controls: ControlsState): number | null {
  return controls.retriever === "hybrid" ? controls.alpha : null;
}

function buildRetrieveRequest(query: string, controls: ControlsState): RetrieveRequest {
  return {
    query,
    dataset: controls.dataset,
    retriever: controls.retriever,
    top_k: controls.topK,
    alpha: alphaValue(controls)
  };
}

function buildRagRequest(query: string, controls: ControlsState): RagRequest {
  return buildRetrieveRequest(query, controls);
}

function loadingText(mode: ControlsState["mode"]): string {
  return mode === "rag" ? "Running retrieval and generating answer with Ollama…" : "Searching…";
}

function submitButtonLabel(mode: ControlsState["mode"]): string {
  return mode === "rag" ? "Ask" : "Retrieve";
}

function RetrievalPanel({ result }: { result: RetrieveResponse }) {
  return (
    <section className="results">
      <div className="results__meta">
        <span>
          retriever: <code>{result.retriever}</code>
        </span>
        {result.alpha !== null && (
          <span>
            α: <code>{result.alpha.toFixed(2)}</code>
          </span>
        )}
        <span>
          top-k: <code>{result.top_k}</code>
        </span>
        <span>
          hits: <code>{result.hits.length}</code>
        </span>
      </div>

      <HitsList hits={result.hits} />
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <a href="/docs" target="_blank" rel="noreferrer">
        Open API docs
      </a>
    </footer>
  );
}

function App() {
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [controls, setControls] = useState<ControlsState>(DEFAULT_CONTROLS);
  const [initialQuery, setInitialQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retrieveResult, setRetrieveResult] = useState<RetrieveResponse | null>(null);
  const [ragResult, setRagResult] = useState<RagResponse | null>(null);
  const [bootError, setBootError] = useState<string | null>(null);

  useEffect(() => {
    // sourcery skip: avoid-function-declarations-in-blocks
    async function bootstrap() {
      try {
        const [config, datasetResponse] = await Promise.all([api.config(), api.datasets()]);

        setDatasets(datasetResponse.datasets);
        setControls((previous) => ({
          ...previous,
          dataset: config.default_dataset,
          retriever: config.default_retriever,
          topK: config.default_top_k,
          alpha: config.default_alpha
        }));
      } catch (err) {
        setBootError((err as Error).message);
      }
    }

    void bootstrap();
  }, []);

  const runQuery = useCallback(
    async (query: string) => {
      setLoading(true);
      setError(null);
      setRetrieveResult(null);
      setRagResult(null);
      setInitialQuery(query);

      try {
        if (controls.mode === "retrieve") {
          setRetrieveResult(await api.retrieve(buildRetrieveRequest(query, controls)));
          return;
        }

        setRagResult(await api.rag(buildRagRequest(query, controls)));
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    },
    [controls]
  );

  return (
    <div className="page">
      <Header />

      {bootError && (
        <div className="banner banner--error">
          Could not load API config: {bootError}. Is <code>uvicorn app:app</code> running?
        </div>
      )}

      <Controls datasets={datasets} state={controls} onChange={setControls} disabled={loading} />

      <QueryBar
        initialQuery={initialQuery}
        loading={loading}
        buttonLabel={submitButtonLabel(controls.mode)}
        onSubmit={runQuery}
      />

      {error && <div className="banner banner--error">Error: {error}</div>}
      {loading && <div className="loading">{loadingText(controls.mode)}</div>}
      {retrieveResult && <RetrievalPanel result={retrieveResult} />}
      {ragResult && <RagAnswerPanel response={ragResult} />}

      <Footer />
    </div>
  );
}

export default App;
