import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API = "http://127.0.0.1:8000/api";

function formatTime(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  const minutes = Math.floor(total / 60);
  const remainingSeconds = total % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainingSeconds).padStart(2, "0")}`;
}

function getList(data, key) {
  return data?.[key] ?? data?.results ?? (Array.isArray(data) ? data : []);
}

function Transcription() {
  const [transcripts, setTranscripts] = useState([]);
  const [videos, setVideos] = useState([]);
  const [segments, setSegments] = useState([]);
  const [selectedVideoId, setSelectedVideoId] = useState("");
  const [selectedTranscriptId, setSelectedTranscriptId] = useState("");
  const [selectedSegments, setSelectedSegments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [captionFile, setCaptionFile] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importMessage, setImportMessage] = useState("");
  const [extractingYouTube, setExtractingYouTube] = useState(false);
  const navigate = useNavigate();

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [transcriptResponse, segmentResponse, videoResponse] = await Promise.all([
        axios.get(`${API}/transcripts/`),
        axios.get(`${API}/transcript-segments/`),
        axios.get(`${API}/videos/`),
      ]);
      const transcriptData = getList(transcriptResponse.data, "transcripts");
      const segmentData = getList(segmentResponse.data, "segments");
      const videoData = getList(videoResponse.data, "videos");

      setTranscripts(transcriptData);
      setSegments(segmentData);
      setVideos(videoData);

      setSelectedVideoId((currentId) =>
        currentId && videoData.some((v) => String(v.id) === String(currentId))
          ? String(currentId)
          : (videoData[0] ? String(videoData[0].id) : "")
      );
      setSelectedTranscriptId((currentId) =>
        currentId && transcriptData.some((t) => String(t.id) === String(currentId))
          ? String(currentId)
          : (transcriptData[0] ? String(transcriptData[0].id) : "")
      );
    } catch (err) {
      console.error("Failed to load transcription data:", err);
      setError("Could not load videos or transcripts. Check Django and the /api/videos/, /api/transcripts/, and /api/transcript-segments/ endpoints.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const currentTranscript = transcripts.find((t) => String(t.id) === String(selectedTranscriptId));
  const selectedVideo = videos.find((v) => String(v.id) === String(selectedVideoId));
  const currentSegments = segments.filter((s) => String(s.transcript) === String(selectedTranscriptId));

  function handleVideoChange(event) {
    const videoId = event.target.value;
    setSelectedVideoId(videoId);
    setError("");
    setImportMessage("");
    const matchingTranscript = transcripts.find((t) => String(t.video) === String(videoId));
    setSelectedTranscriptId(matchingTranscript ? String(matchingTranscript.id) : "");
    setSelectedSegments([]);
  }

  function handleTranscriptChange(event) {
    const transcriptId = event.target.value;
    setSelectedTranscriptId(transcriptId);
    setError("");
    setSelectedSegments([]);
    const transcript = transcripts.find((t) => String(t.id) === String(transcriptId));
    if (transcript) setSelectedVideoId(String(transcript.video));
  }

  function toggleSegment(segmentId) {
    setSelectedSegments((current) =>
      current.includes(segmentId) ? current.filter((id) => id !== segmentId) : [...current, segmentId]
    );
  }

  function selectAllSegments() {
    setSelectedSegments((current) => {
      const allSelected = currentSegments.length > 0 &&
        currentSegments.every((segment) => current.includes(segment.id));
      if (allSelected) {
        return current.filter((id) => !currentSegments.some((s) => s.id === id));
      }
      return [...new Set([...current, ...currentSegments.map((s) => s.id)])];
    });
  }

  async function handleCaptionImport(event) {
    event.preventDefault();
    setImportMessage("");
    setError("");

    if (!selectedVideoId) {
      setError("Choose a saved video before importing captions.");
      return;
    }
    if (!captionFile) {
      setError("Choose an SRT or VTT caption file.");
      return;
    }
    const extension = captionFile.name.split(".").pop()?.toLowerCase();
    if (!["srt", "vtt"].includes(extension)) {
      setError("Please select an .srt or .vtt caption file.");
      return;
    }

    const formData = new FormData();
    formData.append("video_id", selectedVideoId);
    formData.append("caption_file", captionFile);
    setImporting(true);

    try {
      const response = await axios.post(`${API}/transcripts/import-captions/`, formData);
      setImportMessage(`Imported successfully! ${response.data.segment_count} segments saved.`);
      setCaptionFile(null);
      const fileInput = document.getElementById("caption-file-input");
      if (fileInput) fileInput.value = "";
      await loadData();
      if (response.data.transcript_id) setSelectedTranscriptId(String(response.data.transcript_id));
      if (response.data.video_id) setSelectedVideoId(String(response.data.video_id));
    } catch (err) {
      console.error("Caption import failed:", err);
      setError(err.response?.data?.error || "Caption import failed. Check the Django server and try again.");
    } finally {
      setImporting(false);
    }
  }
  
  async function handleYouTubeTranscription() {
    if (!selectedVideoId) {
    setError("Select a YouTube video first.");
    return;
    }

    setExtractingYouTube(true);
    setError("");
    setImportMessage("");
    setSelectedSegments([]);

    try {
      const response = await axios.post(`${API}/transcribe-youtube/`, {
      video_id: selectedVideoId,
    });

    const transcriptId = response.data.transcript_id;
    const videoId = response.data.video_id;

    await loadData();

    if (transcriptId) {
      setSelectedTranscriptId(String(transcriptId));
    }

    if (videoId) {
      setSelectedVideoId(String(videoId));
    }

    setImportMessage(
      `Transcription successful! ${response.data.segment_count} timestamped segments extracted.`
    );
    } catch (err) {
    console.error("YouTube transcription failed:", err);

    setError(
      err.response?.data?.error ||
      err.response?.data?.message ||
      "Could not extract YouTube audio. Check the Django terminal for details."
    );
  } finally {
    setExtractingYouTube(false);
  }
  }


  function sendSelectedSegmentsToClipCreator() {
    const selected = currentSegments.filter((s) => selectedSegments.includes(s.id));
    if (!currentTranscript) {
      setError("Select a transcript that contains timestamped segments.");
      return;
    }
    if (!selected.length) {
      setError("Select at least one transcript segment first.");
      return;
    }
    navigate("/clip-creator", {
      state: {
        videoId: currentTranscript.video,
        transcriptId: currentTranscript.id,
        segments: selected.map((s) => ({
          id: s.id, text: s.text, start_time: s.start_time, end_time: s.end_time,
        })),
      },
    });
  }

  async function copySelectedText() {
    const text = currentSegments
      .filter((s) => selectedSegments.includes(s.id))
      .map((s) => s.text).join(" ");
    if (!text) {
      setError("Select at least one transcript segment first.");
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      setError("");
    } catch {
      setError("Could not copy text to the clipboard.");
    }
  }
  async function handleDeleteSelectedSegments() {
    const selectedIds = currentSegments
    .filter((segment) => selectedSegments.includes(segment.id))
    .map((segment) => segment.id);

    if (!selectedIds.length) {
      setError("Select at least one segment to delete.");
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to permanently delete ${selectedIds.length} selected segment(s)?`
    );

    if (!confirmed) return;

    setError("");
    setImportMessage("");

    try {
      const response = await axios.delete(`${API}/transcript-segments/`, {
        data: {
          segment_ids: selectedIds,
          transcript_id: selectedTranscriptId,
        },
      });

      setSelectedSegments([]);
      await loadData();

      setImportMessage(
        response.data.message || "Selected segments deleted successfully."
      );
    } catch (err) {
      console.error("Failed to delete segments:", err);
      setError(
        err.response?.data?.error ||
        "Could not delete the selected segments. Please try again."
      );
    }
  }


  useEffect(() => { setSelectedSegments([]); }, [selectedTranscriptId]);

  if (loading) return <main style={styles.container}>Loading transcription data...</main>;

  return (
    <main style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Video Transcription</h1>
          <p style={styles.subtitle}>Choose a saved video, import timestamped captions, and select text segments for clips.</p>
        </div>
        <button type="button" style={styles.refreshButton} onClick={loadData}>Refresh</button>
      </div>

      {error && <div style={styles.error} role="alert">{error}</div>}

      <section style={styles.card}>
        <h2 style={styles.sectionTitle}>Select Saved Video</h2>
        <label style={styles.label} htmlFor="saved-video-select">Choose a video for transcription</label>
        <select id="saved-video-select" style={styles.select} value={selectedVideoId} onChange={handleVideoChange}>
          <option value="">Choose a saved video</option>
          {videos.map((video) => <option key={video.id} value={video.id}>{video.title || `Video ${video.id}`}</option>)}
        </select>

        {selectedVideo && (
          <div style={styles.metadata}>
            <p><strong>Title:</strong> {selectedVideo.title}</p>
            <p><strong>Channel:</strong> {selectedVideo.channel || "Unknown"}</p>
            {selectedVideo.url && <p><a href={selectedVideo.url} target="_blank" rel="noreferrer">Open video source</a></p>}
            <div style={{ marginTop: 16 }}>
              <button
              type="button"
              style={styles.refreshButton}
              onClick={handleYouTubeTranscription}
              disabled={extractingYouTube || !selectedVideoId}
              >
                {extractingYouTube
                ? "Extracting audio and transcribing..."
                : "Extract YouTube Segments"}
              </button>
            </div>
          </div>
        )}
        {videos.length === 0 && <p>No saved videos found. Save a video from the YouTube Search page first.</p>}

        <form onSubmit={handleCaptionImport} style={{ marginTop: 24 }}>
          <h2 style={styles.sectionTitle}>Import Captions</h2>
          <p style={styles.subtitle}>Upload a timestamped SRT or VTT caption file for the selected saved video. Use a caption file you are authorized to access.</p>
          <input
            id="caption-file-input"
            type="file"
            accept=".srt,.vtt"
            onChange={(event) => {
              setCaptionFile(event.target.files?.[0] || null);
              setImportMessage("");
              setError("");
            }}
            style={{ display: "block", margin: "16px 0" }}
          />
          <button type="submit" style={styles.refreshButton} disabled={importing || !selectedVideoId || !captionFile}>
            {importing ? "Importing..." : "Import Captions"}
          </button>
          {importMessage && <p style={styles.success} role="status">{importMessage}</p>}
        </form>
      </section>

      <section style={styles.card}>
        <h2 style={styles.sectionTitle}>Saved Transcripts</h2>
        {transcripts.length === 0 ? (
          <p>No transcripts exist yet. Select a saved video above and import an SRT or VTT caption file to create its first transcript.</p>
        ) : (
          <>
            <label style={styles.label} htmlFor="transcript-select">Select a saved transcript</label>
            <select id="transcript-select" style={styles.select} value={selectedTranscriptId} onChange={handleTranscriptChange}>
              <option value="">Choose a transcript</option>
              {transcripts.map((transcript) => (
                <option key={transcript.id} value={transcript.id}>Transcript {transcript.id} — Video {transcript.video}</option>
              ))}
            </select>
            {currentTranscript ? (
              <>
                <p style={styles.metadata}>Video ID: {currentTranscript.video} · Language: {currentTranscript.language || "unknown"}</p>
                <h3 style={styles.sectionTitle}>Full transcript</h3>
                <div style={styles.fullText}>{currentTranscript.full_text || "No transcript text available."}</div>
              </>
            ) : (
              <p style={{ marginTop: 16 }}>This video has no transcript yet. Import captions above to create one.</p>
            )}
          </>
        )}
      </section>

      <section style={styles.card}>
        <div style={styles.segmentHeader}>
          <div>
            <h2 style={styles.sectionTitle}>Timestamped Segments</h2>
            <p style={styles.subtitle}>Select the transcript sections you want to use in your clip.</p>
          </div>
          <button type="button" style={styles.secondaryButton} onClick={selectAllSegments} disabled={!currentTranscript || currentSegments.length === 0}>
            Select / deselect all
          </button>
        </div>

        {!currentTranscript ? (
          <p>Select a transcript above to view its timestamped segments.</p>
        ) : currentSegments.length === 0 ? (
          <p>No timestamped segments found for this transcript.</p>
        ) : (
          <div style={styles.segmentList}>
            {currentSegments.map((segment) => (
              <label key={segment.id} style={styles.segment}>
                <input type="checkbox" checked={selectedSegments.includes(segment.id)} onChange={() => toggleSegment(segment.id)} />
                <span style={styles.timestamp}>{formatTime(segment.start_time)} – {formatTime(segment.end_time)}</span>
                <span style={styles.segmentText}>{segment.text}</span>
              </label>
            ))}
          </div>
        )}

        <div style={styles.footer}>
          <span>{selectedSegments.filter((id) => currentSegments.some((s) => s.id === id)).length} segment(s) selected</span>
          <button
            type="button"
            style={styles.refreshButton}
            onClick={sendSelectedSegmentsToClipCreator}
            disabled={!currentTranscript || !selectedSegments.some((id) => currentSegments.some((s) => s.id === id))}
          >Use Selected Segments</button>
          <button
            type="button"
            style={styles.refreshButton}
            onClick={copySelectedText}
            disabled={!selectedSegments.some((id) => currentSegments.some((s) => s.id === id))}
          >Copy selected text</button>
          <button
            type="button"
            style={{
              ...styles.refreshButton,
              background: "#dc2626",
            }}
            onClick={handleDeleteSelectedSegments}
            disabled={
              !selectedSegments.some((id) =>
                currentSegments.some((segment) => segment.id === id)
            )
            }
          >Delete Selected Segments</button>
        </div>
      </section>
    </main>
  );
}

const styles = {
  container: { maxWidth: 1100, margin: "0 auto", padding: "28px 20px", color: "var(--text-color, #202938)" },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, flexWrap: "wrap", marginBottom: 24 },
  title: { margin: 0, fontSize: 30 },
  subtitle: { color: "#737b89", marginTop: 6, lineHeight: 1.5 },
  card: { background: "var(--card-bg, #ffffff)", border: "1px solid #e1e5eb", borderRadius: 12, padding: 22, marginBottom: 20, overflowWrap: "anywhere" },
  label: { display: "block", fontWeight: 600, marginBottom: 8 },
  select: { width: "100%", padding: 12, border: "1px solid #cbd2dc", borderRadius: 8, background: "white" },
  metadata: { color: "#737b89", fontSize: 14, marginTop: 12, lineHeight: 1.6 },
  sectionTitle: { fontSize: 20, margin: "14px 0" },
  fullText: { padding: 14, background: "#f7f8fa", borderRadius: 8, whiteSpace: "pre-wrap", lineHeight: 1.7 },
  segmentHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" },
  segmentList: { display: "grid", gap: 10 },
  segment: { display: "flex", alignItems: "flex-start", gap: 12, padding: 14, border: "1px solid #e1e5eb", borderRadius: 8, cursor: "pointer" },
  timestamp: { minWidth: 105, fontSize: 13, fontWeight: 600, color: "#3868c8" },
  segmentText: { lineHeight: 1.6 },
  footer: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap", marginTop: 20 },
  refreshButton: { padding: "10px 16px", background: "#2563eb", color: "white", border: 0, borderRadius: 8, cursor: "pointer" },
  secondaryButton: { padding: "9px 12px", background: "#eef2ff", color: "#294bb5", border: 0, borderRadius: 8, cursor: "pointer" },
  error: { padding: 14, marginBottom: 18, background: "#fff1f1", color: "#a52323", borderRadius: 8 },
  success: { color: "#167a3f", marginTop: 12 },
};

export default Transcription;
