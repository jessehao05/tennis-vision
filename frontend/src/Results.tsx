interface Props {
  jobId: string;
  onReset: () => void;
}

export default function Results({ jobId, onReset }: Props) {
  const videoUrl = `/download/video/${jobId}`;
  const heatmapUrl = `/download/heatmap/${jobId}`;

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
      <button className="reset-btn" onClick={onReset}>
        Analyze another video
      </button>
    </div>
  );
}
