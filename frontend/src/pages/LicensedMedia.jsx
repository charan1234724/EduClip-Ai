import { useState } from "react";
import api from "../services/api";

function getDownloadUrl(video) {
  return (
    video.download_url ||
    video.url ||
    video.videos?.large?.url ||
    video.videos?.medium?.url ||
    video.videos?.small?.url ||
    ""
  );
}

function getThumbnail(video) {
  return (
    video.thumbnail ||
    video.picture ||
    video.videos?.medium?.thumbnail ||
    video.videos?.small?.thumbnail ||
    ""
  );
}

function getVideoTitle(video) {
  return video.title || video.tags || `Pixabay video ${video.id ?? ""}`;
}

function LicensedMedia() {
  const [query, setQuery] = useState("");
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [downloadingId, setDownloadingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [downloadedPath, setDownloadedPath] = useState("");

  async function handleSearch(event) {
    event.preventDefault();

    if (!query.trim()) {
      setError("Enter an educational topic to search.");
      setVideos([]);
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    setVideos([]);
    setSelectedVideo(null);
    setDownloadedPath("");

    try {
      // Use the same Pixabay search endpoint as Video Discovery.
      const response = await api.get("/api/licensed-media/pixabay/search/", {
        params: { q: query.trim(), per_page: 20 },
      });

      const data = response.data;
      const results = Array.isArray(data)
        ? data
        : data.videos || data.results || data.hits || [];

      setVideos(results);
      setMessage(
        results.length
          ? `Found ${results.length} Pixabay videos. Select a video and download it to use in Clip Creator.`
          : "No Pixabay videos found. Try a broader keyword or check your Pixabay API configuration."
      );
    } catch (err) {
      console.error("Pixabay media search failed:", err);
      setError(
        err.response?.data?.message ||
          err.response?.data?.error ||
          "Unable to search Pixabay. Check the Django server and Pixabay API configuration."
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleDownload(video) {
    const downloadUrl = getDownloadUrl(video);

    if (!downloadUrl) {
      setError("This Pixabay result does not contain a downloadable video URL.");
      return;
    }

    const itemId = video.id ?? video.video_id ?? getVideoTitle(video);
    setDownloadingId(itemId);
    setError("");
    setMessage("Downloading selected Pixabay footage. Please wait...");
    setDownloadedPath("");

    try {
      const response = await api.post("/api/licensed-media/pixabay/download/", {
        video_id: video.id ?? video.video_id ?? null,
        download_url: downloadUrl,
        source_url: video.pageURL || video.source_url || video.webpage_url || "",
        title: getVideoTitle(video),
        thumbnail: getThumbnail(video),
        duration: video.duration || 0,
        tags: video.tags || "",
      });

      const path =
        response.data?.relative_path ||
        response.data?.media?.relative_path ||
        response.data?.file_path ||
        response.data?.media?.file_path ||
        "";

      if (path) {
        setDownloadedPath(path);
        setMessage(
          `Download successful. Copy this path into Clip Creator: ${path}`
        );
      } else {
        setMessage(
          response.data?.message ||
            "Download request completed, but the response did not include a file path. Check the Django response."
        );
      }
    } catch (err) {
      console.error("Pixabay download failed:", err);
      setMessage("");
      setError(
        err.response?.data?.message ||
          err.response?.data?.error ||
          "Pixabay download failed. Check the Django terminal and download endpoint."
      );
    } finally {
      setDownloadingId(null);
    }
  }

  async function handleCopyPath() {
    if (!downloadedPath) return;

    try {
      await navigator.clipboard.writeText(downloadedPath);
      setMessage("Downloaded video path copied. Paste it into Clip Creator.");
    } catch {
      setError("Could not copy automatically. Select and copy the path manually.");
    }
  }

  return (
    <div className="page">
      <h1>Licensed Media</h1>
      <p>
        Search Pixabay for stock footage, preview the available results, and
        download footage for your narrated educational videos.
      </p>

      <section className="topic-form-card">
        <h2>Search Pixabay videos</h2>

        <form onSubmit={handleSearch}>
          <div className="form-group">
            <label htmlFor="licensed-media-query">Educational topic</label>
            <input
              id="licensed-media-query"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Example: Python programming"
              required
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Searching Pixabay..." : "Search Pixabay"}
          </button>
        </form>

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}
        {message && <p role="status">{message}</p>}

        {downloadedPath && (
          <div style={{ marginTop: "16px" }}>
            <label htmlFor="downloaded-pixabay-path">
              Downloaded video path for Clip Creator
            </label>
            <input
              id="downloaded-pixabay-path"
              type="text"
              value={downloadedPath}
              readOnly
              onFocus={(event) => event.target.select()}
              style={{ width: "100%", boxSizing: "border-box" }}
            />
            <button
              type="button"
              onClick={handleCopyPath}
              style={{ marginTop: "8px" }}
            >
              Copy video path
            </button>
          </div>
        )}
      </section>

      {videos.length > 0 && (
        <section style={{ marginTop: "28px" }}>
          <h2>Pixabay Search Results</h2>

          <div className="dashboard-cards">
            {videos.map((video, index) => {
              const itemId = video.id ?? video.video_id ?? index;
              const title = getVideoTitle(video);
              const thumbnail = getThumbnail(video);
              const isSelected =
                (selectedVideo?.id ?? selectedVideo?.video_id) ===
                (video.id ?? video.video_id);

              return (
                <article className="card" key={itemId}>
                  {thumbnail && (
                    <img
                      src={thumbnail}
                      alt={title}
                      loading="lazy"
                      style={{
                        width: "100%",
                        aspectRatio: "16 / 9",
                        objectFit: "cover",
                        borderRadius: "8px",
                        marginBottom: "12px",
                      }}
                    />
                  )}

                  <h3>{title}</h3>
                  <p>
                    <strong>Provider:</strong> Pixabay
                  </p>
                  {video.duration != null && (
                    <p>
                      <strong>Duration:</strong> {video.duration} seconds
                    </p>
                  )}
                  {video.tags && (
                    <p>
                      <strong>Tags:</strong> {video.tags}
                    </p>
                  )}
                  {(video.pageURL || video.source_url || video.webpage_url) && (
                    <p>
                      <a
                        href={video.pageURL || video.source_url || video.webpage_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        View Pixabay source and license
                      </a>
                    </p>
                  )}

                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedVideo(video);
                        setError("");
                        setMessage("");
                      }}
                    >
                      {isSelected ? "Selected" : "Select Video"}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDownload(video)}
                      disabled={
                        downloadingId !== null ||
                        !getDownloadUrl(video)
                      }
                    >
                      {downloadingId === itemId
                        ? "Downloading..."
                        : "Download for Clip Creator"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {selectedVideo && (
        <section
          className="topic-form-card"
          style={{ marginTop: "28px" }}
          aria-live="polite"
        >
          <h2>Selected Pixabay Video</h2>
          <p>
            <strong>Title:</strong> {getVideoTitle(selectedVideo)}
          </p>
          <p>
            <strong>Provider:</strong> Pixabay
          </p>
          <p>
            Download this footage to save it locally before generating your
            narrated MP4.
          </p>
          <button
            type="button"
            onClick={() => handleDownload(selectedVideo)}
            disabled={downloadingId !== null || !getDownloadUrl(selectedVideo)}
          >
            {downloadingId !== null
              ? "Downloading..."
              : "Download Selected Video"}
          </button>
          <button
            type="button"
            onClick={() => {
              setSelectedVideo(null);
              setError("");
            }}
            style={{ marginLeft: "8px" }}
            disabled={downloadingId !== null}
          >
            Clear Selection
          </button>
        </section>
      )}
    </div>
  );
}

export default LicensedMedia;
