import { useMemo, useState } from "react";

import type { Hit, RagResponse } from "../api";
import { HitsList } from "./HitsList";
import { MarkdownContent, normalizeMarkdown } from "./MarkdownContent";

interface Props {
  response: RagResponse;
}

interface CitationToken {
  id: string;
  valid: boolean;
}

type AnswerPart = string | CitationToken;

function normalizeCitationId(raw: string): string {
  return raw
    .replace(/^chunk_id\s*=\s*/i, "")
    .replace(/^citation\s*:\s*/i, "")
    .split("|")[0]
    .replace(/[.,;:]+$/g, "")
    .trim();
}

function chunkIds(hits: Hit[]): Set<string> {
  return new Set(hits.map((hit) => hit.chunk_id));
}

function findCitationAt(answer: string, index: number, known: Set<string>): CitationToken | null {
  if (answer[index] !== "[") {
    return null;
  }

  const end = answer.indexOf("]", index + 1);

  if (end === -1) {
    return null;
  }

  const raw = answer.slice(index + 1, end);
  const id = normalizeCitationId(raw);

  if (!known.has(id)) {
    return null;
  }

  return { id, valid: true };
}

function splitAnswer(answer: string, known: Set<string>): AnswerPart[] {
  const normalized = normalizeMarkdown(answer);
  const parts: AnswerPart[] = [];
  let buffer = "";
  let index = 0;

  while (index < normalized.length) {
    const citation = findCitationAt(normalized, index, known);

    if (citation) {
      if (buffer) {
        parts.push(buffer);
        buffer = "";
      }

      parts.push(citation);
      index = normalized.indexOf("]", index) + 1;
      continue;
    }

    buffer += normalized[index];
    index += 1;
  }

  if (buffer) {
    parts.push(buffer);
  }

  return parts;
}

function citationIds(answer: string, known: Set<string>): string[] {
  return splitAnswer(answer, known)
    .filter((part): part is CitationToken => typeof part !== "string")
    .map((part) => part.id);
}

function citedChunkIds(answer: string, hits: Hit[]): Set<string> {
  const known = chunkIds(hits);
  return new Set(citationIds(answer, known));
}

function inventedCitationIds(answer: string, hits: Hit[]): string[] {
  const known = chunkIds(hits);
  const normalized = normalizeMarkdown(answer);
  const bracketTokens = [...normalized.matchAll(/\[([^\]]+)\]/g)];

  return bracketTokens
    .map((match) => normalizeCitationId(match[1]))
    .filter((id) => id.includes("::"))
    .filter((id) => !known.has(id));
}

function CitationChip({ citation }: { citation: CitationToken }) {
  return (
    <span className="citation" title={`Citation: ${citation.id}`}>
      [{citation.id}]
    </span>
  );
}

function AnnotatedMarkdown({ text, known }: { text: string; known: Set<string> }) {
  const parts = useMemo(() => splitAnswer(text, known), [text, known]);

  return (
    <>
      {parts.map((part, index) =>
        typeof part === "string" ? (
          <MarkdownContent key={index} text={part} inline />
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
        <AnnotatedMarkdown text={response.answer} known={known} />
      </article>

      <button
        className="rag__prompt-toggle"
        type="button"
        onClick={() => setShowPrompt((value) => !value)}
        aria-expanded={showPrompt}
      >
        {showPrompt ? "Hide" : "Show"} full prompt sent to the LLM
      </button>

      {showPrompt && (
        <div className="rag__prompt markdown-prompt">
          <MarkdownContent text={response.prompt} />
        </div>
      )}

      <h3 className="rag__hits-title">Retrieved chunks</h3>
      <HitsList hits={response.hits} highlight={cited} />
    </section>
  );
}
