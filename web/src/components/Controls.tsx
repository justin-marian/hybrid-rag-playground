import type { DatasetInfo, RetrieverName } from "../api";

export type Mode = "retrieve" | "rag";

export interface ControlsState {
  dataset: string;
  retriever: RetrieverName;
  topK: number;
  alpha: number;
  mode: Mode;
}

interface Props {
  datasets: DatasetInfo[];
  state: ControlsState;
  onChange: (next: ControlsState) => void;
  disabled: boolean;
}

const RETRIEVERS: { value: RetrieverName; label: string }[] = [
  { value: "bm25", label: "BM25" },
  { value: "dense", label: "Dense" },
  { value: "hybrid", label: "Hybrid" }
];

const MODES: { value: Mode; label: string }[] = [
  { value: "retrieve", label: "Retrieve" },
  { value: "rag", label: "RAG" }
];

function datasetLabel(dataset: DatasetInfo): string {
  if (dataset.indexed_count === null) {
    return dataset.name;
  }

  return `${dataset.name} (${dataset.indexed_count.toLocaleString()} chunks)`;
}

function buttonClass(isActive: boolean): string {
  return isActive ? "segmented__btn segmented__btn--on" : "segmented__btn";
}

export function Controls({ datasets, state, onChange, disabled }: Props) {
  const update = <K extends keyof ControlsState>(key: K, value: ControlsState[K]) => {
    onChange({ ...state, [key]: value });
  };

  return (
    <section className="controls">
      <label className="field">
        <span>Dataset</span>
        <select
          value={state.dataset}
          onChange={(event) => update("dataset", event.target.value)}
          disabled={disabled || datasets.length === 0}
        >
          {datasets.map((dataset) => (
            <option key={dataset.key} value={dataset.key}>
              {datasetLabel(dataset)}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Retriever</span>
        <select
          value={state.retriever}
          onChange={(event) => update("retriever", event.target.value as RetrieverName)}
          disabled={disabled}
        >
          {RETRIEVERS.map((retriever) => (
            <option key={retriever.value} value={retriever.value}>
              {retriever.label}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Top-k: {state.topK}</span>
        <input
          type="range"
          min={1}
          max={20}
          step={1}
          value={state.topK}
          onChange={(event) => update("topK", Number(event.target.value))}
          disabled={disabled}
        />
      </label>

      <label className={`field ${state.retriever !== "hybrid" ? "field--muted" : ""}`}>
        <span>Alpha: {state.alpha.toFixed(2)}</span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={state.alpha}
          onChange={(event) => update("alpha", Number(event.target.value))}
          disabled={disabled || state.retriever !== "hybrid"}
        />
      </label>

      <fieldset className="field field--mode">
        <span>Mode</span>
        <div className="segmented">
          {MODES.map((mode) => (
            <button
              key={mode.value}
              type="button"
              className={buttonClass(state.mode === mode.value)}
              onClick={() => update("mode", mode.value)}
              disabled={disabled}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </fieldset>
    </section>
  );
}
