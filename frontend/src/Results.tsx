import { useEffect, useState } from "react";

interface SummaryRow {
  player: string;
  total_shots: string;
  errors: string;
  in_bounds_shots: string;
  avg_shot_speed_kmh: string;
  max_shot_speed_kmh: string;
  avg_player_speed_kmh: string;
  max_player_speed_kmh: string;
  total_rallies: string;
  longest_rally: string;
  avg_rally_length: string;
}

interface PerShotRow {
  shot_number: string;
  hitting_player: string;
  ball_speed_kmh: string;
  player_1_speed_kmh: string;
  player_2_speed_kmh: string;
  ball_in_bounds: string;
  rally_number: string;
}

interface Accuracy {
  total_shots: number;
  tracking_quality_pct: number;
  ball_speed: {
    mean: number | null;
    min: number | null;
    max: number | null;
    outliers: number;
    threshold_low: number;
    threshold_high: number;
  };
  player_speed: {
    p1_flagged: number;
    p2_flagged: number;
    threshold: number;
  };
  rally: {
    total: number;
    avg_length: number | null;
    longest: number | null;
    shortest: number | null;
  };
}

interface StatsData {
  summary: SummaryRow[];
  per_shot: PerShotRow[];
  accuracy: Accuracy;
}

interface Props {
  jobId: string;
  onReset: () => void;
}

const SUMMARY_LABELS: { key: keyof SummaryRow; label: string }[] = [
  { key: "total_shots",         label: "Total Shots" },
  { key: "in_bounds_shots",     label: "In Bounds" },
  { key: "errors",              label: "Errors" },
  { key: "avg_shot_speed_kmh",  label: "Avg Shot Speed (km/h)" },
  { key: "max_shot_speed_kmh",  label: "Max Shot Speed (km/h)" },
  { key: "avg_player_speed_kmh",label: "Avg Player Speed (km/h)" },
  { key: "max_player_speed_kmh",label: "Max Player Speed (km/h)" },
  { key: "total_rallies",       label: "Total Rallies" },
  { key: "longest_rally",       label: "Longest Rally" },
  { key: "avg_rally_length",    label: "Avg Rally Length" },
];

export default function Results({ jobId, onReset }: Props) {
  const videoUrl = `/download/video/${jobId}`;
  const heatmapUrl = `/download/heatmap/${jobId}`;
  const [stats, setStats] = useState<StatsData | null>(null);

  useEffect(() => {
    fetch(`/stats/${jobId}`)
      .then((r) => r.ok ? r.json() : null)
      .then((data) => data && setStats(data))
      .catch(() => {});
  }, [jobId]);

  const p1 = stats?.summary.find((r) => r.player === "1");
  const p2 = stats?.summary.find((r) => r.player === "2");

  return (
    <div className="results">
      <div className="results-grid">
        <div className="result-panel">
          <h2>Output Video</h2>
          <video controls src={videoUrl} />
          <a href={videoUrl} download={`${jobId}.mp4`} className="download-btn">
            Download Video
          </a>
        </div>
        <div className="result-panel">
          <h2>Shot Heatmap</h2>
          <img src={heatmapUrl} alt="Shot heatmap" />
          <a href={heatmapUrl} download={`${jobId}.png`} className="download-btn">
            Download Heatmap
          </a>
        </div>
      </div>

      {stats?.accuracy && Object.keys(stats.accuracy).length > 0 && (
        <div className="stats-section">
          <h2 className="stats-title">Pipeline Accuracy</h2>
          <div className="accuracy-grid">

            <div className="accuracy-card">
              <div className="accuracy-card-label">Tracking Quality</div>
              <div className={`accuracy-card-value ${stats.accuracy.tracking_quality_pct >= 90 ? "good" : stats.accuracy.tracking_quality_pct >= 70 ? "warn" : "bad"}`}>
                {stats.accuracy.tracking_quality_pct}%
              </div>
              <div className="accuracy-card-sub">
                {stats.accuracy.ball_speed.outliers} outlier shot{stats.accuracy.ball_speed.outliers !== 1 ? "s" : ""} out of {stats.accuracy.total_shots}
              </div>
            </div>

            <div className="accuracy-card">
              <div className="accuracy-card-label">Ball Speed Range</div>
              <div className="accuracy-card-value neutral">
                {stats.accuracy.ball_speed.min ?? "—"} – {stats.accuracy.ball_speed.max ?? "—"} km/h
              </div>
              <div className="accuracy-card-sub">
                avg {stats.accuracy.ball_speed.mean ?? "—"} km/h &nbsp;·&nbsp; expected 10–250
              </div>
            </div>

            <div className="accuracy-card">
              <div className="accuracy-card-label">Player Speed Flags</div>
              <div className={`accuracy-card-value ${stats.accuracy.player_speed.p1_flagged + stats.accuracy.player_speed.p2_flagged === 0 ? "good" : "warn"}`}>
                P1: {stats.accuracy.player_speed.p1_flagged} &nbsp;·&nbsp; P2: {stats.accuracy.player_speed.p2_flagged}
              </div>
              <div className="accuracy-card-sub">shots where player speed &gt; {stats.accuracy.player_speed.threshold} km/h</div>
            </div>

            <div className="accuracy-card">
              <div className="accuracy-card-label">Rally Distribution</div>
              <div className="accuracy-card-value neutral">
                {stats.accuracy.rally.avg_length ?? "—"} avg shots
              </div>
              <div className="accuracy-card-sub">
                {stats.accuracy.rally.total} rallies &nbsp;·&nbsp; longest {stats.accuracy.rally.longest ?? "—"} &nbsp;·&nbsp; shortest {stats.accuracy.rally.shortest ?? "—"}
              </div>
            </div>

          </div>
        </div>
      )}

      {p1 && p2 && (
        <div className="stats-section">
          <div className="stats-header">
            <h2 className="stats-title">Match Stats</h2>
            <a href={`/download/csv/summary/${jobId}`} download="match_summary.csv" className="download-btn">
              Download CSV
            </a>
          </div>
          <table className="stats-table">
            <thead>
              <tr>
                <th>Stat</th>
                <th>Player 1</th>
                <th>Player 2</th>
              </tr>
            </thead>
            <tbody>
              {SUMMARY_LABELS.map(({ key, label }) => (
                <tr key={key}>
                  <td className="stat-label">{label}</td>
                  <td>{p1[key] ?? "—"}</td>
                  <td>{p2[key] ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {stats!.per_shot.length > 0 && (
            <>
              <div className="stats-header" style={{ marginTop: "2rem" }}>
                <h2 className="stats-title">Per Shot</h2>
                <a href={`/download/csv/per-shot/${jobId}`} download="per_shot_stats.csv" className="download-btn">
                  Download CSV
                </a>
              </div>
              <div className="per-shot-scroll">
                <table className="stats-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Rally</th>
                      <th>Player</th>
                      <th>Ball Speed (km/h)</th>
                      <th>P1 Speed (km/h)</th>
                      <th>P2 Speed (km/h)</th>
                      <th>In Bounds</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats!.per_shot.map((row) => (
                      <tr key={row.shot_number} className={row.ball_in_bounds === "False" ? "out-of-bounds" : ""}>
                        <td>{row.shot_number}</td>
                        <td>{row.rally_number}</td>
                        <td>{row.hitting_player}</td>
                        <td>{row.ball_speed_kmh}</td>
                        <td>{row.player_1_speed_kmh}</td>
                        <td>{row.player_2_speed_kmh}</td>
                        <td>{row.ball_in_bounds === "True" ? "✓" : "✗"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      <button className="reset-btn" onClick={onReset}>
        Analyze another video
      </button>
    </div>
  );
}