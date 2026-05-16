import { useState } from "react";

import type { Hit } from "../api";

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
  return text.length > 280;
}

export function HitsList({ hits, highlight }: Props) {
  if (hits.length === 0) {
    return <p className="empty">No hits to show.</p>;
  }

  return (
    <ul className="hits">
      {hits.map((hit) => (
        <HitItem key={hit.chunk_id} hit={hit} highlighted={highlight?.has(hit.chunk_id)} />
      ))}
    </ul>
  );
}

function HitItem({ hit, highlighted }: HitItemProps) {
  const [open, setOpen] = useState(false);

  const toggleOpen = () => setOpen((value) => !value);

  return (
    <li className={hitClass(highlighted)}>
      <header className="hit__header" onClick={toggleOpen}>
        <span className="hit__rank">#{hit.rank}</span>
        <span className="hit__chunk">{hit.chunk_id}</span>
        <span className="hit__score">score {hit.score.toFixed(3)}</span>
        {highlighted && <span className="hit__cited-tag">cited</span>}
      </header>

      {hit.title && <h4 className="hit__title">{hit.title}</h4>}

      <p className={`hit__text ${open ? "hit__text--open" : ""}`}>{hit.text}</p>

      {shouldShowToggle(hit.text) && (
        <button className="hit__toggle" type="button" onClick={toggleOpen}>
          {open ? "Show less" : "Show more"}
        </button>
      )}
    </li>
  );
}
