
import { useEffect, useState } from "react";
import api from "../services/api";

function GeneratedClips() {
  const [clips, setClips] = useState([]);
  const [videos, setVideos] = useState([]);
  const [narratedFiles, setNarratedFiles] = useState([]);

  const [loading, setLoading] = useState(true);
  const [narratedLoading, setNarratedLoading] = useState(true);
  const [error, setError] = useState("");

  const getMediaUrl = (relativeUrl) => {
    const url = String(relativeUrl || "").replace(/\\/g, "/");

    if (/^https?:\/\//i.test(url)) {
      return url;
    }

    const baseURL = api.defaults?.baseURL || "";
    const origin = baseURL.startsWith("http")
      ? new URL(baseURL).origin
      : window.location.origin;

    return `${origin}/${url.replace(/^\/+/, "")}`;
  };

  const loadData = async () => {
    setError("");
    setLoading(true);
    setNarratedLoading(true);

    try {
      const [clipsResponse, videosResponse] = await Promise.all([
        api.get("/api/clips/"),
        api.get("/api/videos/"),
      ]);

      setClips(clipsResponse.data.clips || []);
      setVideos(videosResponse.data.videos || []);
    } catch (err) {
      console.error("Unable to load saved clips:", err);
      setError("Unable to load saved clip records.");
    } finally {
      setLoading(false);
    }

    try {
      const response = await api.get("/api/narrated-clips/");
      setNarratedFiles(response.data.clips || []);
    } catch (err) {
      console.error("Unable to load narrated videos:", err);
      setError((previous) =>
        previous
          ? `${previous} Unable to load generated videos.`
          : "Unable to load generated videos."
      );
    } finally {
      setNarratedLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getVideoTitle = (videoId) => {
    const video = videos.find(
      (item) => item.id === Number(videoId)
    );

    return video ? video.title : `Video ID: ${videoId}`;
  };

  const formatFileSize = (bytes) => {
    const size = Number(bytes) || 0;

    return size < 1024 * 1024
      ? `${(size / 1024).toFixed(1)} KB`
      : `${(size / (1024 * 1024)).toFixed(2)} MB`;
  };
  async function handleDeleteNarratedVideo(file) {
    const confirmed = window.confirm(
      `Permanently delete "${file.filename}"?`
    );
    if (!confirmed) return;
    try {
      await axios.delete(`${API}/narrated-clips/`, {
        data: { filename: file.filename },
      });
      setNarratedFiles((currentFiles) =>
        currentFiles.filter(
          (item) => item.filename !== file.filename
        )
      );
    window.alert("Video deleted successfully.");
  } catch (error) {
    console.error("Failed to delete narrated video:", error);

    window.alert(
      error.response?.data?.message ||
        "Could not delete the video. Please try again."
    );
  }
}


  return (
    <div className="page">
      <h1>Generated Clips</h1>

      <p>
        Watch and download generated educational videos, and review
        your saved clip records.
      </p>

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      <section className="dashboard-section">
        <h2>Generated Narrated Videos</h2>
        {narratedLoading ? (
          <p>Loading generated videos...</p>
        ) : narratedFiles.length === 0 ? (
        <div className="empty-state">
          <h3>No generated videos yet</h3>
          <p>
            Generate an MP4 from Clip Creator to see it here.
            </p>
            </div>
            ) : (
            <div className="dashboard-cards">
              {narratedFiles.map((file) => {
                const videoURL = getMediaUrl(file.url);
                return (
                <div className="card" key={file.filename}>
                  <h3>{file.title || file.filename}</h3>
                  <video
              controls
              preload="metadata"
              src={videoURL}
              style={{
                display: "block",
                width: "100%",
                borderRadius: "8px",
                background: "#000",
              }}
            >
              Your browser does not support video playback.
            </video>

            <p>
              <strong>File:</strong> {file.filename}
            </p>

            <p>
              <strong>Size:</strong>{" "}
              {formatFileSize(file.size_bytes)}
            </p>

            <a
              href={videoURL}
              download={file.filename}
              target="_blank"
              rel="noreferrer"
            >
              Download Video
            </a>

            <button
              type="button"
              onClick={() => handleDeleteNarratedVideo(file)}
              style={{
                marginTop: "16px",
                backgroundColor: "#dc2626",
                color: "#ffffff",
                border: "none",
                borderRadius: "8px",
                padding: "10px 16px",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              Delete Video
            </button>
          </div>
        );
      })}
    </div>
  )}
    </section>

      {/* Existing saved clip records */}
      <section className="dashboard-section">
        <h2>Saved Clips</h2>

        {loading ? (
          <p>Loading saved clips...</p>
        ) : clips.length === 0 ? (
          <div className="empty-state">
            <h3>No saved clip records</h3>
            <p>
              Clip records saved through Clip Creator will appear here.
            </p>
          </div>
        ) : (
          <div className="dashboard-cards">
            {clips.map((clip) => (
              <div className="card" key={clip.id}>
                <h3>
                  {clip.title || getVideoTitle(clip.video)}
                </h3>

                <p>
                  <strong>Start:</strong> {clip.start_time}s
                </p>

                <p>
                  <strong>End:</strong> {clip.end_time}s
                </p>

                <p>
                  <strong>Duration:</strong>{" "}
                  {(
                    Number(clip.end_time) -
                    Number(clip.start_time)
                  ).toFixed(1)}
                  s
                </p>

                {(clip.custom_text || clip.text) && (
                  <p>
                    <strong>Text:</strong>{" "}
                    {clip.custom_text || clip.text}
                  </p>
                )}

                <p>
                  <strong>Output:</strong>{" "}
                  {clip.output_file || "No output linked"}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default GeneratedClips;
