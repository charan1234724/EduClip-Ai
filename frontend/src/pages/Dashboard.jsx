
import { useEffect, useState } from "react";
import api from "../services/api";

function Dashboard() {
  const [stats, setStats] = useState({
    topics: 0,
    videos: 0,
    transcripts: 0,
    clips: 0,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setError("");

        const [
          topicsResponse,
          videosResponse,
          transcriptsResponse,
          clipsResponse,
        ] = await Promise.all([
          api.get("/api/topics/"),
          api.get("/api/videos/"),
          api.get("/api/transcripts/"),
          api.get("/api/clips/"),
        ]);

        setStats({
          topics: topicsResponse.data.count,
          videos: videosResponse.data.count,
          transcripts: transcriptsResponse.data.count,
          clips: clipsResponse.data.count,
        });
      } catch (err) {
        console.error(err);
        setError(
          "Unable to load all dashboard statistics. Check that the backend APIs are running."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <p>
        Welcome to EduClip AI, your AI-powered educational
        video content curator.
      </p>

      {loading && <p>Loading dashboard...</p>}

      {error && (
        <p className="error-message">🔴 {error}</p>
      )}

      {!loading && !error && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-label">
                Educational Topics
              </span>
              <strong className="stat-value">
                {stats.topics}
              </strong>
              <span className="stat-description">
                Topics stored
              </span>
            </div>

            <div className="stat-card">
              <span className="stat-label">Videos</span>
              <strong className="stat-value">
                {stats.videos}
              </strong>
              <span className="stat-description">
                Videos stored
              </span>
            </div>

            <div className="stat-card">
              <span className="stat-label">Transcripts</span>
              <strong className="stat-value">
                {stats.transcripts}
              </strong>
              <span className="stat-description">
                Transcripts stored
              </span>
            </div>

            <div className="stat-card">
              <span className="stat-label">
                Generated Clips
              </span>
              <strong className="stat-value">
                {stats.clips}
              </strong>
              <span className="stat-description">
                Clip records stored
              </span>
            </div>
          </div>

          <div className="dashboard-section">
            <h2>Content Curation Workflow</h2>

            <div className="workflow-grid">
              <div className="workflow-card">
                <span>01</span>
                <h3>Generate Topics</h3>
                <p>
                  Discover educational topics with strong
                  content potential.
                </p>
              </div>

              <div className="workflow-card">
                <span>02</span>
                <h3>Discover Videos</h3>
                <p>
                  Find relevant educational videos for
                  selected topics.
                </p>
              </div>

              <div className="workflow-card">
                <span>03</span>
                <h3>Transcribe</h3>
                <p>
                  Convert video audio into timestamped
                  transcripts.
                </p>
              </div>

              <div className="workflow-card">
                <span>04</span>
                <h3>Create Clips</h3>
                <p>
                  Select useful content for short-form
                  educational videos.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default Dashboard;
