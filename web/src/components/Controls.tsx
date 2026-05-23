import type { DatasetInfo, RetrieverName } from "../api";
import { SelectField } from "./SelectField";

export type Mode = "retrieve" | "generate";

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
  { value: "hybrid", label: "Hybrid" },
];

const MODES: { value: Mode; label: string }[] = [
  { value: "retrieve", label: "Retrieve" },
  { value: "generate", label: "Generate" },
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
  const safeDatasets = Array.isArray(datasets) ? datasets : [];
  const hasDatasets = safeDatasets.length > 0;

  const datasetOptions = hasDatasets
    ? safeDatasets.map((dataset) => ({
        value: dataset.key,
        label: datasetLabel(dataset),
      }))
    : [{ value: "", label: "No datasets available" }];

  const update = <K extends keyof ControlsState>(key: K, value: ControlsState[K]) => {
    onChange({ ...state, [key]: value });
  };

  const alphaMuted = state.retriever !== "hybrid";

  return (
    <section className="controls" aria-label="Pipeline configuration">
      <label className="field">
        <span>Dataset</span>
        <SelectField
          value={hasDatasets ? state.dataset : ""}
          options={datasetOptions}
          onChange={(value) => update("dataset", value)}
          disabled={disabled || !hasDatasets}
          ariaLabel="Dataset"
        />
      </label>

      <label className="field">
        <span>Retriever</span>
        <SelectField
          value={state.retriever}
          options={RETRIEVERS}
          onChange={(value) => update("retriever", value as RetrieverName)}
          disabled={disabled}
          ariaLabel="Retriever"
        />
      </label>

      <label className="field field--range">
        <span>
          Top-k
          <span className="field__value">{state.topK}</span>
        </span>
        <input
          type="range"
          min={1}
          max={20}
          step={1}
          value={state.topK}
          onChange={(event) => update("topK", Number(event.target.value))}
          disabled={disabled}
          aria-label="Top-k"
        />
      </label>

      <label className={`field field--range ${alphaMuted ? "field--muted" : ""}`}>
        <span>
          Alpha
          <span className="field__value">{state.alpha.toFixed(2)}</span>
        </span>
        <input
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={state.alpha}
          onChange={(event) => update("alpha", Number(event.target.value))}
          disabled={disabled || alphaMuted}
          aria-label="Alpha (hybrid retriever blend)"
        />
      </label>

      <fieldset className="field field--mode">
        <span>Mode</span>
        <div className="segmented" role="tablist" aria-label="Mode">
          {MODES.map((mode) => (
            <button
              key={mode.value}
              type="button"
              role="tab"
              aria-selected={state.mode === mode.value}
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
