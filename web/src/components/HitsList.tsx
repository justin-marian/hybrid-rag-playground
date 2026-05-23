import { useState } from "react";

import type { Hit } from "../api";
import { MarkdownContent } from "./MarkdownContent";

interface Props {
  hits: Hit[];
  highlight?: Set<string>;
}

interface HitItemProps {
  hit: Hit;
  highlighted?: boolean;
}

function hitClass(highlighted?: boolean): string {
  return highlighted ? "hit hit--cited" : "hit";
}

function shouldShowToggle(text: string): boolean {
  return text.trim().length > 180;
}

export function HitsList({ hits, highlight }: Props) {
  if (hits.length === 0) {
    return <p className="empty">No hits to show.</p>;
  }

  return (
    <ul className="hits">
      {hits.map((hit) => (
        <HitItem
          key={hit.chunk_id}
          hit={hit}
          highlighted={highlight?.has(hit.chunk_id)}
        />
      ))}
    </ul>
  );
}

function HitItem({ hit, highlighted }: HitItemProps) {
  const [open, setOpen] = useState(false);
  const showToggle = shouldShowToggle(hit.text);

  const toggleOpen = () => setOpen((value) => !value);

  return (
    <li className={hitClass(highlighted)}>
      <header
        className="hit__header"
        onClick={toggleOpen}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            toggleOpen();
          }
        }}
        aria-expanded={open}
      >
        <span className="hit__rank">#{hit.rank}</span>

        <span className="hit__chunk" title={hit.chunk_id}>
          {hit.chunk_id}
        </span>

        <span className="hit__score">score {hit.score.toFixed(3)}</span>

        {highlighted && <span className="hit__cited-tag">cited</span>}
      </header>

      {hit.title && <h4 className="hit__title">{hit.title}</h4>}

      <div className="hit__body">
        <div className={`hit__text ${open ? "hit__text--open" : ""}`}>
          <MarkdownContent text={hit.text} className="hit__markdown" />
        </div>

        {showToggle && (
          <button
            className={`hit__toggle ${open ? "hit__toggle--open" : ""}`}
            type="button"
            onClick={toggleOpen}
            aria-expanded={open}
          >
            {open ? "Show less" : "Show more"}
          </button>
        )}
      </div>
    </li>
  );
}
