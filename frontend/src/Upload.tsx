import { useState, useRef, DragEvent, ChangeEvent } from "react";

interface Props {
  onDone: (jobId: string) => void;
}

export default function Upload({ onDone }: Props) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function selectFile(file: File) {
    setSelectedFile(file);
    setError(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(file));
  }

  async function startAnalysis() {
    if (!selectedFile) return;
    setUploading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", selectedFile);
      const res = await fetch("/upload", { method: "POST", body: form });
      if (!res.ok) throw new Error(`Upload failed (${res.status})`);
      const { job_id } = await res.json();
      onDone(job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
      setUploading(false);
    }
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) selectFile(file);
  }

  function onChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) selectFile(file);
  }

  if (selectedFile && previewUrl) {
    return (
      <div className="upload-preview">
        <video src={previewUrl} controls className="preview-video" />
        <p className="preview-filename">{selectedFile.name}</p>
        {error && <p className="error">{error}</p>}
        <div className="preview-actions">
          <button
            className="reset-btn secondary"
            onClick={() => { setSelectedFile(null); setPreviewUrl(null); }}
            disabled={uploading}
          >
            Choose different video
          </button>
          <button className="reset-btn" onClick={startAnalysis} disabled={uploading}>
            {uploading ? "Uploading..." : "Analyze video"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`dropzone ${dragging ? "dragging" : ""}`}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <input
        ref={inputRef}
        type="file"
        accept="video/*"
        style={{ display: "none" }}
        onChange={onChange}
      />
      <p>Drag and drop a video file here</p>
      <p className="hint">or click to browse</p>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
