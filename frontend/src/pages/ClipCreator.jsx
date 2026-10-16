import axios from "axios";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";


function formatTime(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  const minutes = Math.floor(total / 60);
  const remainingSeconds = total % 60;

  return `${String(minutes).padStart(2, "0")}:${String(
    remainingSeconds
  ).padStart(2, "0")}`;
}

function ClipCreator() {
  const location = useLocation();
  const navigate = useNavigate();

  const selectedData = location.state || {};
  const selectedSegments = selectedData.segments || [];
  const videoId = selectedData.videoId || "";
  const transcriptId = selectedData.transcriptId || "";

  const [customText, setCustomText] = useState("");
  const [preparedClip, setPreparedClip] = useState(null);
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [savedClip, setSavedClip] = useState(null);
  const [enhancing, setEnhancing] = useState(false);
  const [enhancedText, setEnhancedText] = useState("");
  const [enhancementMessage, setEnhancementMessage] = useState("");

  // Generate an MP4 with AI narration over downloaded Pixabay footage.
  const [sourceVideoPath, setSourceVideoPath] = useState("");
  const [narrationVoice, setNarrationVoice] = useState("en-US-AriaNeural");
  const [generatingNarratedClip, setGeneratingNarratedClip] = useState(false);
  const [narratedClipError, setNarratedClipError] = useState("");
  const [narratedClipMessage, setNarratedClipMessage] = useState("");
  const [narratedClip, setNarratedClip] = useState(null);

  const transcriptText = selectedSegments
    .map((segment) => segment.text)
    .join(" ")
    .trim();

  const finalText = customText.trim() || transcriptText;

  const validSegments = selectedSegments.filter(
    (segment) =>
      Number.isFinite(Number(segment.start_time)) &&
      Number.isFinite(Number(segment.end_time)) &&
      Number(segment.start_time) >= 0 &&
      Number(segment.end_time) > Number(segment.start_time)
  );

  const startTime =
    validSegments.length > 0
      ? Math.min(
          ...validSegments.map((segment) =>
            Number(segment.start_time)
          )
        )
      : null;

  const endTime =
    validSegments.length > 0
      ? Math.max(
          ...validSegments.map((segment) =>
            Number(segment.end_time)
          )
        )
      : null;

  function handlePrepareClip() {
    setMessage("");
    setPreparedClip(null);

    if (!videoId) {
      setMessage(
        "No saved video ID found. Return to Transcription and select segments again."
      );
      return;
    }

    if (validSegments.length === 0) {
      setMessage(
        "Select at least one valid timestamped transcript segment."
      );
      return;
    }

    if (!finalText) {
      setMessage("Clip text cannot be empty.");
      return;
    }

    const clipSpecification = {
      video_id: Number(videoId),
      transcript_id: transcriptId ? Number(transcriptId) : null,
      title: "Educational Short Clip",
      start_time: startTime,
      end_time: endTime,
      duration: Number((endTime - startTime).toFixed(2)),
      text: finalText,
      segments: validSegments.map((segment) => ({
        id: segment.id,
        start_time: Number(segment.start_time),
        end_time: Number(segment.end_time),
        text: segment.text,
      })),
      aspect_ratio: "9:16",
      status: "prepared",
    };

    setPreparedClip(clipSpecification);
    setMessage(
      "Clip specification prepared successfully. It is ready for the next backend integration step."
    );
  }
  async function handleSaveClip() {
    if (!preparedClip) {
      setSaveMessage("Prepare the clip data first.");
        return;
  }

  setSaving(true);
  setSaveMessage("");
  setSavedClip(null);

  try {
    const response = await axios.post(
      "http://127.0.0.1:8000/api/clips/",
      {
        video: preparedClip.video_id,
        title: preparedClip.title,
        start_time: preparedClip.start_time,
        end_time: preparedClip.end_time,
        text: preparedClip.text,
        status: preparedClip.status,
      }
    );

    const clip = response.data.clip;

    setSavedClip(clip);
    setSaveMessage(
      `Clip saved successfully. Database ID: ${clip.id}`
    );
  } catch (error) {
    console.error("Failed to save clip:", error);

    const details = error.response?.data?.errors;

    setSaveMessage(
      details
        ? `The backend rejected some fields: ${JSON.stringify(details)}`
        : error.response?.data?.message ||
            "Unable to save the clip. Check that Django is running."
    );
  } finally {
      setSaving(false);
    }
  }

  async function handleEnhanceAI() {
    const sourceText = finalText.trim();

      if (!sourceText) {
        setEnhancementMessage(
        "Select transcript segments or enter custom text first."
      );
      return;
  }

  setEnhancing(true);
  setEnhancedText("");
  setEnhancementMessage("");

  try {
    const response = await axios.post(
      "http://127.0.0.1:8000/api/ai/enhance-clip/",
      { text: sourceText }
    );

    const result = response.data.enhanced_text;

    if (!result || !result.trim()) {
      throw new Error("The AI returned an empty script.");
    }

    setEnhancedText(result.trim());
    setEnhancementMessage(
      "AI enhancement completed. Review the script below before using it."
    );
  } catch (error) {
    console.error("AI script enhancement failed:", error);

    setEnhancementMessage(
      error.response?.data?.message ||
        error.message ||
        "Could not enhance the script. Check Django and OpenRouter."
    );
  } finally {
    setEnhancing(false);
  }
}


async function handleGenerateNarratedClip() {
  const script = finalText.trim();
  const videoPath = sourceVideoPath.trim();

  if (!videoPath) {
    setNarratedClipError(
      "Download a Pixabay video from Licensed Media, then enter its relative file path."
    );
    return;
  }

  if (!script) {
    setNarratedClipError(
      "Select transcript segments or enter narration text first."
    );
    return;
  }

  if (
    startTime === null ||
    endTime === null ||
    endTime <= startTime
  ) {
    setNarratedClipError(
      "Select at least one valid timestamped transcript segment."
    );
    return;
  }

  setGeneratingNarratedClip(true);
  setNarratedClipError("");
  setNarratedClipMessage("");
  setNarratedClip(null);

  try {
    const response = await axios.post(
      "http://127.0.0.1:8000/api/narrated-clips/generate/",
      {
        video_path: videoPath,
        text: script,
        voice: narrationVoice,
        start_time: startTime,
        end_time: endTime,
      }
    );

    setNarratedClip(response.data.clip || null);
    setNarratedClipMessage(
      response.data.message ||
        "Narrated educational video generated successfully."
    );
  } catch (error) {
    console.error("Narrated clip generation failed:", error);

    setNarratedClipError(
      error.response?.data?.message ||
        "Unable to generate the narrated clip. Check Django and FFmpeg."
    );
  } finally {
    setGeneratingNarratedClip(false);
  }
}

function getNarratedClipUrl(relativePath) {
  if (!relativePath) return "";
  const normalizedPath = String(relativePath)
  .split("\\")
  .join("/")
  .replace(/^\/+/, "");
  return `http://127.0.0.1:8000/media/${normalizedPath}`;
}

function handleUseEnhancedText() {
  if (!enhancedText.trim()) return;

  setCustomText(enhancedText.trim());
  setPreparedClip(null);
  setSavedClip(null);
  setMessage("");
  setSaveMessage("");
  setEnhancementMessage("Enhanced script selected as the clip text.");
}



  return (
    <div className="page">
      <h1>Clip Creator</h1>

      <p>
        Prepare your selected transcript or custom text for a
        short-form educational video.
      </p>

      <section className="topic-form-card">
        <h2>Selected Transcript Segments</h2>

        {selectedSegments.length === 0 ? (
          <div className="empty-state">
            <h3>No segments selected</h3>
            <p>
              Open Transcription, select timestamped segments,
              and click Use Selected Segments.
            </p>
          </div>
        ) : (
          <>
            <p>
              <strong>Video ID:</strong> {videoId}
            </p>
            <p>
              <strong>Transcript ID:</strong>{" "}
              {transcriptId || "Not provided"}
            </p>
            <p>
              <strong>Selected segments:</strong>{" "}
              {selectedSegments.length}
            </p>
            <p>
              <strong>Valid segments:</strong>{" "}
              {validSegments.length}
            </p>
            {startTime !== null && endTime !== null && (
              <p>
                <strong>Clip time range:</strong>{" "}
                {formatTime(startTime)} – {formatTime(endTime)}
              </p>
            )}

            {selectedSegments.map((segment, index) => (
              <div
                key={segment.id ?? index}
                style={{
                  padding: "12px",
                  marginBottom: "10px",
                  border: "1px solid #ddd",
                  borderRadius: "8px",
                }}
              >
                <strong>
                  {formatTime(segment.start_time)} –{" "}
                  {formatTime(segment.end_time)}
                </strong>
                <p>{segment.text}</p>
              </div>
            ))}
          </>
        )}
      </section>

      <section className="topic-form-card">
        <h2>Custom Text</h2>
        <p>
          Leave this empty to use the selected transcript text.
          Enter your own text to replace it.
        </p>

        <textarea
          value={customText}
          onChange={(event) => {
            setCustomText(event.target.value);
            setPreparedClip(null);
            setMessage("");
          }}
          placeholder="Enter your educational video script..."
          rows={6}
          style={{
            width: "100%",
            padding: "12px",
            boxSizing: "border-box",
            border: "1px solid #ccc",
            borderRadius: "8px",
            resize: "vertical",
          }}
        />

        <h3>Final Text Preview</h3>
        <div
          style={{
            padding: "14px",
            background: "#f7f8fa",
            borderRadius: "8px",
            whiteSpace: "pre-wrap",
            lineHeight: 1.7,
            overflowWrap: "anywhere",
          }}
        >
          {finalText || "Your final clip text will appear here."}
        </div>

        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
            marginTop: "20px",
          }}
        >
          <div style={{ marginTop: "20px" }}>
            <button
            type="button"
            onClick={handleEnhanceAI}
            disabled={enhancing || !finalText.trim()}
            >
            {enhancing ? "Enhancing script..." : "Enhance with AI"}
            </button>
            {enhancementMessage && (
            <p role="status">{enhancementMessage}</p>
            )}
          </div>
          {enhancedText && (
            <div style={{ marginTop: "20px" }}>
              <h3>AI-Enhanced Script</h3>
              <div
              style={{
                padding: "14px",
                background: "#f0fdf4",
                borderRadius: "8px",
                whiteSpace: "pre-wrap",
                lineHeight: 1.7,
                overflowWrap: "anywhere",
              }}
              >
              {enhancedText}
              </div>
              <button
                type="button"
                onClick={handleUseEnhancedText}
                style={{ marginTop: "12px" }}
              >
                Use Enhanced Script
              </button>
              </div>
            )}

          <button type="button" onClick={handlePrepareClip}>
            Prepare Clip Data
          </button>

          <button
            type="button"
            onClick={() => navigate("/transcription")}
          >
            Back to Transcription
          </button>
        </div>

        {message && (
          <p role="status" style={{ marginTop: "16px" }}>
            {message}
          </p>
        )}
      </section>

      
      <section className="topic-form-card">
        <h2>Generate Narrated MP4</h2>

        <p>
          Use downloaded Pixabay stock footage with your final script and AI
          voice narration. This creates a new educational video, not a clip of
          the original YouTube footage.
        </p>

        <div className="form-group">
          <label htmlFor="source-video-path">Downloaded Pixabay video path</label>
          <input
            id="source-video-path"
            type="text"
            value={sourceVideoPath}
            onChange={(event) => {
              setSourceVideoPath(event.target.value);
              setNarratedClipError("");
            }}
            placeholder="pixabay_downloads/your_video.mp4"
          />
          <small>
            Download a video from Licensed Media and paste its returned relative_path here.
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="narration-voice">Narration voice</label>
          <select
            id="narration-voice"
            value={narrationVoice}
            onChange={(event) => setNarrationVoice(event.target.value)}
          >
            <option value="en-US-AriaNeural">English (US) — Aria</option>
            <option value="en-US-GuyNeural">English (US) — Guy</option>
            <option value="en-GB-SoniaNeural">English (UK) — Sonia</option>
            <option value="en-IN-NeerjaNeural">English (India) — Neerja</option>
            <option value="en-IN-PrabhatNeural">English (India) — Prabhat</option>
          </select>
        </div>

        <p>
          <strong>Narration source:</strong>{" "}
          {finalText
            ? `${finalText.length} characters from Final Text Preview`
            : "No text available"}
        </p>

        <p>
          <strong>Clip time range:</strong>{" "}
          {startTime !== null && endTime !== null
            ? `${formatTime(startTime)} – ${formatTime(endTime)}`
            : "No valid timestamps"}
        </p>

        <button
          type="button"
          onClick={handleGenerateNarratedClip}
          disabled={
            generatingNarratedClip ||
            !sourceVideoPath.trim() ||
            !finalText.trim() ||
            startTime === null ||
            endTime === null ||
            endTime <= startTime
          }
        >
          {generatingNarratedClip
            ? "Generating MP4 with narration..."
            : "Generate Narrated MP4"}
        </button>

        {narratedClipError && (
          <p className="error-message" role="alert" style={{ marginTop: "12px" }}>
            {narratedClipError}
          </p>
        )}

        {narratedClipMessage && (
          <p role="status" style={{ marginTop: "12px" }}>
            {narratedClipMessage}
          </p>
        )}

        {narratedClip && (
          <div style={{ marginTop: "18px" }}>
            <h3>Your narrated clip is ready</h3>
            <p><strong>File:</strong> {narratedClip.relative_path}</p>
            {narratedClip.size_bytes && (
              <p>
                <strong>Size:</strong>{" "}
                {(narratedClip.size_bytes / (1024 * 1024)).toFixed(2)} MB
              </p>
            )}
            <video
              controls
              preload="metadata"
              src={getNarratedClipUrl(narratedClip.relative_path)}
              style={{ width: "100%", maxWidth: "720px", borderRadius: "8px" }}
            >
              Your browser does not support HTML video.
            </video>
            <p>
              <a
                href={getNarratedClipUrl(narratedClip.relative_path)}
                download={narratedClip.filename || "educlip-narrated.mp4"}
                target="_blank"
                rel="noreferrer"
              >
                Open or download narrated MP4
              </a>
            </p>
          </div>
        )}
      </section>


      {preparedClip && (
        <section className="topic-form-card">
          <h2>Prepared Clip Specification</h2>
          <p>
            <strong>Duration:</strong>{" "}
            {preparedClip.duration} seconds
          </p>
          <p>
            <strong>Aspect ratio:</strong>{" "}
            {preparedClip.aspect_ratio}
          </p>
          <p>
            <strong>Status:</strong> {preparedClip.status}
          </p>

          <pre
            style={{
              padding: "14px",
              background: "#f7f8fa",
              borderRadius: "8px",
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
            }}
          >
            {JSON.stringify(preparedClip, null, 2)}
          </pre>

          <button
            type="button"
            onClick={() =>
              navigator.clipboard.writeText(
                JSON.stringify(preparedClip, null, 2)
              )
            }
          >
            Copy Clip Specification
          </button>
          <button
            type="button"
            onClick={handleSaveClip}
              disabled={saving}
          >
            {saving ? "Saving..." : "Save Clip to Database"}
          </button>

          {saveMessage && (
            <p role="status">{saveMessage}</p>
          )}

          {savedClip && (
          <p>
            Saved clip ID: {savedClip.id}
          </p>
          )}
        </section>
      )}
    </div>
  );
}

export default ClipCreator;
