import { useEffect, useState } from "react";

import { api, type HealthResponse } from "../api";

type StatusLabel = "loading" | "ok" | "degraded" | "unreachable";

const HEALTH_POLL_MS = 15_000;

function healthStatus(health: HealthResponse | null, error: string | null): StatusLabel {
  if (error) {
    return "unreachable";
  }

  return health?.status ?? "loading";
}

function HealthDetail({ health }: { health: HealthResponse | null }) {
  if (!health) {
    return null;
  }

  const weaviateStatus = health.weaviate_ready ? "Ready" : "Offline";
  const ollamaStatus = health.llm_reachable ? "Ready" : "Offline";

  return (
    <span className="pill__detail">
      Weaviate: {weaviateStatus} | Ollama: {ollamaStatus}
    </span>
  );
}

function LogoMark() {
  return (
    <span className="header__logo" aria-hidden="true">
      <img src="/icons/ollama-tool.png" alt="" draggable={false} />
    </span>
  );
}

export function Header() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    // comment:avoid-function-declarations-in-blocks
    async function pollHealth() {
      try {
        const response = await api.health();

        if (cancelled) {
          return;
        }

        setHealth(response);
        setError(null);
      } catch (err) {
        if (cancelled) {
          return;
        }

        setHealth(null);
        setError((err as Error).message);
      }
    }

    void pollHealth();

    const intervalId = window.setInterval(pollHealth, HEALTH_POLL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, []);

  const status = healthStatus(health, error);

  return (
    <header className="header">
      <div className="header__left">
        <LogoMark />
        <div className="header__title">
          <h1>Hybrid RAG Pipeline</h1>
          <span className="header__subtitle">
            BEIR · Weaviate · Ollama Local
          </span>
        </div>
      </div>

      <div className="header__right">
        <span className="badge" aria-hidden="true">
          <span className="badge__icon" />
          Experimenting RAG Setups
        </span>
        <div
          className={`pill pill--${status}`}
          role="status"
          aria-live="polite"
          title={error ?? health?.detail ?? undefined}
        >
          <span className="pill__dot" />
          <span className="pill__label">API: {status}</span>
          <HealthDetail health={health} />
        </div>
      </div>
    </header>
  );
}
