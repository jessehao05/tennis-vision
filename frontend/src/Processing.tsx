import { useEffect, useState } from "react";

interface Props {
  jobId: string;
  onDone: () => void;
}

export default function Processing({ jobId, onDone }: Props) {
  const [progress, setProgress] = useState("Starting...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/status/${jobId}`);
        if (!res.ok) throw new Error(`Status check failed (${res.status})`);
        const data = await res.json();
        setProgress(data.progress);

        if (data.status === "done") {
          clearInterval(interval);
          onDone();
        } else if (data.status === "failed") {
          clearInterval(interval);
          setError(data.error ?? "Processing failed");
        }
      } catch (e) {
        clearInterval(interval);
        setError(e instanceof Error ? e.message : "Unknown error");
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId, onDone]);

  return (
    <div className="processing">
      {error ? (
        <p className="error">{error}</p>
      ) : (
        <>
          <div className="spinner" />
          <p className="progress-message">{progress}</p>
        </>
      )}
    </div>
  );
}
