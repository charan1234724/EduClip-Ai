
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

function Videos() {
  const navigate = useNavigate();
  const [videos, setVideos] = useState([]);
  const [topics, setTopics] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTopicId, setSelectedTopicId] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [searchMessage, setSearchMessage] = useState("");

  const [formData, setFormData] = useState({
    topic: "",
    youtube_id: "",
    title: "",
    channel: "",
    url: "",
    thumbnail: "",
    view_count: "",
    duration: "",
  });

  const fetchVideos = async () => {
    try {
      const response = await api.get("/api/videos/");
      setVideos(response.data.videos || []);
      setError("");
    } catch (err) {
      console.error(err);
      setError("Unable to load saved videos from the backend.");
    } finally {
      setLoading(false);
    }
  };

  const fetchTopics = async () => {
    try {
      const response = await api.get("/api/topics/");
      setTopics(response.data.topics || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchVideos();
    fetchTopics();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  };

  const handleSearch = async (event) => {
    event.preventDefault();

    if (!searchQuery.trim()) {
      setSearchError("Enter a topic or keyword to search.");
      setSearchResults([]);
      return;
    }

    try {
      setSearching(true);
      setSearchError("");
      setSearchMessage("");
      setSearchResults([]);

      const response = await api.get("/api/youtube/search/", {
        params: {
          q: searchQuery.trim(),
          max_results: 9,
        },
      });

      const results = response.data.videos || [];
      setSearchResults(results);

      if (results.length === 0) {
        setSearchMessage("No videos found. Try another search term.");
      } else {
        setSearchMessage(`Found ${results.length} videos.`);
      }
    } catch (err) {
      console.error(err);

      const message = err.response?.data?.message;
      setSearchError(
        message || "Unable to search YouTube. Check your backend and API configuration."
      );
    } finally {
      setSearching(false);
    }
  };

  const handleSelectVideo = async (video) => {
    setError("");
    setSearchError("");
    setSearchMessage("");

    // A saved video must be linked to one of the generated topics.
    if (!selectedTopicId) {
      setSearchError(
        "Choose a generated topic in the Search YouTube section first, then click Select Video."
      );
      document.getElementById("topic-search")?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      return;
    }

    setSearching(true);
    try {
      // Reuse an existing database record if this YouTube video was saved before.
      const savedResponse = await api.get("/api/videos/");
      const savedVideos = savedResponse.data.videos || [];
      let savedVideo = savedVideos.find(
        (item) => String(item.youtube_id) === String(video.youtube_id)
      );

      if (!savedVideo) {
        const payload = {
          topic: Number(selectedTopicId),
          youtube_id: video.youtube_id,
          title: video.title,
          channel: video.channel || "",
          url: video.url,
          thumbnail: video.thumbnail || "",
          view_count: Number(video.view_count ?? 0),
          duration: video.duration || "",
        };
        const response = await api.post("/api/videos/", payload);
        savedVideo = response.data.video || response.data;
        if (!savedVideo.id) {
          const refreshed = await api.get("/api/videos/");
          savedVideo = (refreshed.data.videos || []).find(
            (item) => String(item.youtube_id) === String(video.youtube_id)
          );
        }
      }

      if (!savedVideo?.id) {
        throw new Error("The video was saved, but its database ID could not be found.");
      }

      setSearchMessage("Video selected. Opening Video Transcription...");
      navigate("/transcription", {
        state: {
          selectedVideoId: String(savedVideo.id),
          youtubeId: video.youtube_id,
          videoTitle: video.title,
          videoUrl: video.url,
        },
      });
    } catch (err) {
      console.error("Could not select YouTube video:", err);
      const detail = err.response?.data?.errors || err.response?.data?.error || err.response?.data?.detail;
      setSearchError(
        typeof detail === "string"
          ? detail
          : detail
          ? JSON.stringify(detail)
          : err.message || "Could not save the selected video. Check the Django server."
      );
    } finally {
      setSearching(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      setError("");
      setSearchMessage("");

      const newVideo = {
        topic: Number(formData.topic),
        youtube_id: formData.youtube_id,
        title: formData.title,
        channel: formData.channel,
        url: formData.url,
        thumbnail: formData.thumbnail,
        view_count: Number(formData.view_count),
        duration: formData.duration,
      };

      await api.post("/api/videos/", newVideo);

      setFormData({
        topic: "",
        youtube_id: "",
        title: "",
        channel: "",
        url: "",
        thumbnail: "",
        view_count: "",
        duration: "",
      });

      await fetchVideos();
      setSearchMessage("Video saved successfully to your database.");
    } catch (err) {
      console.error(err);

      if (err.response?.data?.errors) {
        setError(JSON.stringify(err.response.data.errors));
      } else if (err.response?.data) {
        setError(JSON.stringify(err.response.data));
      } else {
        setError("Unable to save the video. Check your backend connection.");
      }
    }
  };

  const formatViews = (count) =>
    Number(count || 0).toLocaleString("en-IN");

  const formatDuration = (duration) => {
    if (!duration) return "Not available";

    // Convert YouTube ISO 8601 durations, such as PT1H2M10S,
    // into a readable format such as 1:02:10.
    const match = duration.match(
      /^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$/
    );

    if (!match) return duration;

    const hours = Number(match[1] || 0);
    const minutes = Number(match[2] || 0);
    const seconds = Number(match[3] || 0);

    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, "0")}:${String(
        seconds
      ).padStart(2, "0")}`;
    }

    return `${minutes}:${String(seconds).padStart(2, "0")}`;
  };
  async function handleRemoveVideo(video) {
    const confirmed = window.confirm(
      `Are you sure you want to remove "${video.title}" from Saved Videos?`
    );

    if (!confirmed) return;

      try {
      setError("");

      await axios.delete(`${API}/videos/`, {
        data: { video_id: video.id },
      });

      setVideos((currentVideos) =>
        currentVideos.filter((item) => item.id !== video.id)
      );
      } catch (err) {
        console.error("Failed to remove saved video:", err);
      setError(
        err.response?.data?.error ||
        "Could not remove the video. Please try again."
      );
    }
  }


  return (
    <div className="page">
      <h1>Video Discovery</h1>

      <p>
        Discover educational videos on YouTube and save selected videos
        to your EduClip AI database.
      </p>

      {/* YouTube Search */}
      <div className="topic-form-card">
        <h2>Search YouTube</h2>

        <form onSubmit={handleSearch}>
          <div className="form-group">
            <label htmlFor="topic-search">
              Search using a generated topic
            </label>

            <select
              id="topic-search"
              value={selectedTopicId}
              onChange={(event) => {
              const topicId = event.target.value;
              setSelectedTopicId(topicId);

              const selectedTopic = topics.find(
                (topic) => String(topic.id) === topicId
              );

              if (selectedTopic) {
                setSearchQuery(selectedTopic.title);
              }
              }}
            >
            <option value="">Choose a topic or search manually</option>

            {topics.map((topic) => (
              <option key={topic.id} value={topic.id}>
              {topic.title}
              </option>
            ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="youtube-search">
              Educational topic or keyword
            </label>

            <input
              id="youtube-search"
              type="search"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Example: Python programming for beginners"
              required
            />
          </div>

          <button type="submit" disabled={searching}>
            {searching ? "Searching YouTube..." : "Search Videos"}
          </button>
        </form>

        {searchError && (
          <p className="error-message" role="alert">
            {searchError}
          </p>
        )}

        {searchMessage && (
          <p role="status" style={{ marginTop: "12px" }}>
            {searchMessage}
          </p>
        )}
      </div>

      {/* YouTube Search Results */}
      {searchResults.length > 0 && (
        <section style={{ marginTop: "28px" }}>
          <h2>YouTube Search Results</h2>

          <div className="dashboard-cards">
            {searchResults.map((video) => (
              <div className="card" key={video.youtube_id}>
                {video.thumbnail && (
                  <a
                    href={video.url}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Watch ${video.title} on YouTube`}
                  >
                    <img
                      src={video.thumbnail}
                      alt={video.title}
                      loading="lazy"
                      style={{
                        width: "100%",
                        aspectRatio: "16 / 9",
                        objectFit: "cover",
                        borderRadius: "8px",
                        marginBottom: "12px",
                      }}
                    />
                  </a>
                )}

                <h3>{video.title}</h3>

                <p>
                  <strong>Channel:</strong>{" "}
                  {video.channel || "Unknown"}
                </p>

                <p>
                  <strong>Views:</strong>{" "}
                  {formatViews(video.view_count)}
                </p>

                <p>
                  <strong>Duration:</strong>{" "}
                  {formatDuration(video.duration)}
                </p>

                {video.published_at && (
                  <p>
                    <strong>Published:</strong>{" "}
                    {new Date(video.published_at).toLocaleDateString()}
                  </p>
                )}

                <div
                  style={{
                    display: "flex",
                    gap: "10px",
                    flexWrap: "wrap",
                    marginTop: "12px",
                  }}
                >
                  <a
                    href={video.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Watch on YouTube
                  </a>

                  <button
                    type="button"
                    onClick={() => handleSelectVideo(video)}
                    disabled={searching}
                  >
                    {searching ? "Opening..." : "Select Video & Transcribe"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Existing Add Video Form */}
      <div
        className="topic-form-card"
        id="add-video-form"
        style={{ marginTop: "30px" }}
      >
        <h2>Add Video to Database</h2>

        <p>
          Use “Select Video &amp; Transcribe” on a YouTube result to save it and
          open the transcription workflow. This form remains available for manual entries.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="video-topic">Topic</label>

            <select
              id="video-topic"
              name="topic"
              value={formData.topic}
              onChange={handleChange}
              required
            >
              <option value="">Select a topic</option>

              {topics.map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.title}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="youtube-id">YouTube Video ID</label>

            <input
              id="youtube-id"
              type="text"
              name="youtube_id"
              value={formData.youtube_id}
              onChange={handleChange}
              placeholder="YouTube video ID"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="video-title">Video Title</label>

            <input
              id="video-title"
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="Enter video title"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="video-channel">Channel</label>

            <input
              id="video-channel"
              type="text"
              name="channel"
              value={formData.channel}
              onChange={handleChange}
              placeholder="Channel name"
            />
          </div>

          <div className="form-group">
            <label htmlFor="video-url">YouTube URL</label>

            <input
              id="video-url"
              type="url"
              name="url"
              value={formData.url}
              onChange={handleChange}
              placeholder="https://www.youtube.com/watch?v=..."
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="video-thumbnail">Thumbnail URL</label>

            <input
              id="video-thumbnail"
              type="url"
              name="thumbnail"
              value={formData.thumbnail}
              onChange={handleChange}
              placeholder="https://..."
            />
          </div>

          <div className="form-group">
            <label htmlFor="video-views">View Count</label>

            <input
              id="video-views"
              type="number"
              name="view_count"
              value={formData.view_count}
              onChange={handleChange}
              placeholder="Number of views"
              min="0"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="video-duration">Duration</label>

            <input
              id="video-duration"
              type="text"
              name="duration"
              value={formData.duration}
              onChange={handleChange}
              placeholder="Example: PT8M32S or 08:32"
            />
          </div>

          <button type="submit">Add Video</button>
        </form>
      </div>

      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}

      {/* Existing Saved Videos */}
      <section style={{ marginTop: "30px" }}>
        <h2>Saved Videos</h2>

        {loading && <p>Loading saved videos...</p>}

        {!loading && !error && videos.length === 0 && (
          <div className="empty-state">
            <h3>No saved videos available</h3>
            <p>
              Search YouTube and select a video, or add a video manually
              using the form above.
            </p>
          </div>
        )}

        {!loading && videos.length > 0 && (
          <div className="dashboard-cards">
            {videos.map((video) => (
              <div className="card" key={video.id}>
                {video.thumbnail && (
                  <img
                    src={video.thumbnail}
                    alt={video.title}
                    loading="lazy"
                    style={{
                      width: "100%",
                      aspectRatio: "16 / 9",
                      objectFit: "cover",
                      borderRadius: "8px",
                      marginBottom: "15px",
                    }}
                  />
                )}

                <h3>{video.title}</h3>
                <p>
                  <strong>Educational Topic:</strong>{" "}
                  {video.topic_title || "Topic not available"}
                </p>

                <p>
                  <strong>Channel:</strong>{" "}
                  {video.channel || "Unknown"}
                </p>

                <p>
                  <strong>Views:</strong>{" "}
                  {formatViews(video.view_count)}
                </p>

                <p>
                  <strong>Duration:</strong>{" "}
                  {formatDuration(video.duration)}
                </p>

                <a
                  href={video.url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Watch on YouTube
                </a>
                <div style={{ marginTop: "16px" }}>
                  <button
                  type="button"
                  onClick={() => handleRemoveVideo(video)}
                  style={{
                    backgroundColor: "#dc2626",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "8px",
                    padding: "10px 16px",
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                  >Remove Video</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default Videos;
