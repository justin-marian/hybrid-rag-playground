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

  return (
    <span className="pill__detail">
      wv:{health.weaviate_ready ? "✓" : "✗"} · ol:
      {health.ollama_reachable ? "✓" : "✗"}
    </span>
  );
}

export function Header() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

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
      <div className="header__title">
        <h1>Hybrid RAG Pipeline</h1>
        <span className="header__subtitle">BEIR · Weaviate · Ollama · Local LLM</span>
      </div>

      <div className={`pill pill--${status}`} title={error ?? health?.detail ?? undefined}>
        <span className="pill__dot" />
        <span>API: {status}</span>
        <HealthDetail health={health} />
      </div>
    </header>
  );
}
