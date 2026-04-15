import { useState } from "react";
import Upload from "./Upload";
import Processing from "./Processing";
import Results from "./Results";

type View = "upload" | "processing" | "results";

export default function App() {
  const [view, setView] = useState<View>("upload");
  const [jobId, setJobId] = useState<string | null>(null);

  function handleUploadDone(id: string) {
    setJobId(id);
    setView("processing");
  }

  function handleProcessingDone() {
    setView("results");
  }

  function handleReset() {
    setJobId(null);
    setView("upload");
  }

  return (
    <div className="app">
      <header>
        <h1>Tennis Vision</h1>
      </header>
      <main>
        {view === "upload" && <Upload onDone={handleUploadDone} />}
        {view === "processing" && jobId && (
          <Processing jobId={jobId} onDone={handleProcessingDone} />
        )}
        {view === "results" && jobId && (
          <Results jobId={jobId} onReset={handleReset} />
        )}
      </main>
    </div>
  );
}
