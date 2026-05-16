import { useMemo, useState } from "react";

import type { Hit, RagResponse } from "../api";
import { HitsList } from "./HitsList";

interface Props {
  response: RagResponse;
}

interface CitationToken {
  id: string;
  valid: boolean;
}

type AnswerPart = string | CitationToken;

const CITATION_RE = /\[(?:chunk_id\s*=\s*)?([^\]\s|]+)\]/g;

function chunkIds(hits: Hit[]): Set<string> {
  return new Set(hits.map((hit) => hit.chunk_id));
}

function citationIds(answer: string): string[] {
  const ids: string[] = [];
  const re = new RegExp(CITATION_RE.source, "g");
  let match: RegExpExecArray | null;

  while ((match = re.exec(answer)) !== null) {
    ids.push(match[1]);
  }

  return ids;
}

function splitAnswer(answer: string, known: Set<string>): AnswerPart[] {
  const parts: AnswerPart[] = [];
  const re = new RegExp(CITATION_RE.source, "g");
  let last = 0;
  let match: RegExpExecArray | null;

  while ((match = re.exec(answer)) !== null) {
    if (match.index > last) {
      parts.push(answer.slice(last, match.index));
    }

    parts.push({ id: match[1], valid: known.has(match[1]) });
    last = match.index + match[0].length;
  }

  if (last < answer.length) {
    parts.push(answer.slice(last));
  }

  return parts;
}

function citedChunkIds(answer: string, hits: Hit[]): Set<string> {
  const known = chunkIds(hits);
  return new Set(citationIds(answer).filter((id) => known.has(id)));
}

function inventedCitationIds(answer: string, hits: Hit[]): string[] {
  const known = chunkIds(hits);
  return citationIds(answer).filter((id) => !known.has(id));
}

function CitationChip({ citation }: { citation: CitationToken }) {
  return (
    <span
      className={`citation ${citation.valid ? "" : "citation--bad"}`}
      title={citation.id}
    >
      [{citation.id}]
    </span>
  );
}

function Annotated({ text, known }: { text: string; known: Set<string> }) {
  const parts = useMemo(() => splitAnswer(text, known), [text, known]);

  return (
    <>
      {parts.map((part, index) =>
        typeof part === "string" ? (
          <span key={index}>{part}</span>
        ) : (
          <CitationChip key={index} citation={part} />
        ),
      )}
    </>
  );
}

export function RagAnswerPanel({ response }: Props) {
  const [showPrompt, setShowPrompt] = useState(false);

  const known = useMemo(() => chunkIds(response.hits), [response.hits]);
  const cited = useMemo(
    () => citedChunkIds(response.answer, response.hits),
    [response.answer, response.hits],
  );
  const invented = useMemo(
    () => inventedCitationIds(response.answer, response.hits),
    [response.answer, response.hits],
  );

  return (
    <section className="rag">
      <div className="rag__meta">
        <span>
          model: <code>{response.model}</code>
        </span>
        <span>
          retriever: <code>{response.retriever}</code>
        </span>
        {response.alpha !== null && (
          <span>
            alpha: <code>{response.alpha.toFixed(2)}</code>
          </span>
        )}
        <span>
          top-k: <code>{response.top_k}</code>
        </span>
        <span>
          citations: <code>{cited.size}/{response.hits.length}</code>
        </span>
        {invented.length > 0 && (
          <span className="rag__warn" title={invented.join(", ")}>
            {invented.length} invented citation{invented.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      <article className="rag__answer">
        <Annotated text={response.answer} known={known} />
      </article>

      <button
        className="rag__prompt-toggle"
        type="button"
        onClick={() => setShowPrompt((value) => !value)}
      >
        {showPrompt ? "Hide" : "Show"} full prompt sent to the LLM
      </button>

      {showPrompt && <pre className="rag__prompt">{response.prompt}</pre>}

      <h3 className="rag__hits-title">Retrieved chunks</h3>
      <HitsList hits={response.hits} highlight={cited} />
    </section>
  );
}
