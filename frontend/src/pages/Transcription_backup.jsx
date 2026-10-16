
import { useEffect, useState } from "react";
import api from "../services/api";

function Transcription() {
  const [transcripts, setTranscripts] = useState([]);
  const [videos, setVideos] = useState([]);
  const [segments, setSegments] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [transcriptForm, setTranscriptForm] = useState({
    video: "",
    full_text: "",
    language: "en",
  });

  const [segmentForm, setSegmentForm] = useState({
    transcript: "",
    text: "",
    start_time: "",
    end_time: "",
  });

  const fetchVideos = async () => {
    const response = await api.get("/api/videos/");
    setVideos(response.data.videos);
  };

  const fetchTranscripts = async () => {
    const response = await api.get("/api/transcripts/");
    setTranscripts(response.data.transcripts);
  };

  const fetchSegments = async () => {
    const response = await api.get("/api/transcript-segments/");
    setSegments(response.data.segments);
  };

  const loadData = async () => {
    try {
      setError("");

      await Promise.all([
        fetchVideos(),
        fetchTranscripts(),
        fetchSegments(),
      ]);
    } catch (err) {
      console.error(err);
      setError("Unable to load transcription data. Check the Django APIs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTranscriptChange = (event) => {
    const { name, value } = event.target;

    setTranscriptForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSegmentChange = (event) => {
    const { name, value } = event.target;

    setSegmentForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const saveTranscript = async (event) => {
    event.preventDefault();

    try {
      setError("");
      setSuccess("");

      await api.post("/api/transcripts/", {
        video: Number(transcriptForm.video),
        full_text: transcriptForm.full_text,
        language: transcriptForm.language,
      });

      setTranscriptForm({
        video: "",
        full_text: "",
        language: "en",
      });

      await fetchTranscripts();

      setSuccess("Transcript saved successfully.");
    } catch (err) {
      console.error(err);
      setError(
        JSON.stringify(
          err.response?.data?.errors ||
          err.response?.data ||
          "Unable to save transcript."
        )
      );
    }
  };

  const saveSegment = async (event) => {
    event.preventDefault();

    const startTime = Number(segmentForm.start_time);
    const endTime = Number(segmentForm.end_time);

    if (endTime <= startTime) {
      setError("End time must be greater than start time.");
      return;
    }

    try {
      setError("");
      setSuccess("");

      await api.post("/api/transcript-segments/", {
        transcript: Number(segmentForm.transcript),
        text: segmentForm.text.trim(),
        start_time: startTime,
        end_time: endTime,
      });

      setSegmentForm({
        transcript: segmentForm.transcript,
        text: "",
        start_time: "",
        end_time: "",
      });

      await fetchSegments();

      setSuccess("Transcript segment saved successfully.");
    } catch (err) {
      console.error(err);
      setError(
        JSON.stringify(
          err.response?.data?.errors ||
          err.response?.data ||
          "Unable to save transcript segment."
        )
      );
    }
  };

  const getVideoTitle = (videoId) => {
    const video = videos.find(
      (item) => item.id === Number(videoId)
    );

    return video ? video.title : `Video ID: ${videoId}`;
  };

  const getTranscriptTitle = (transcriptId) => {
    const transcript = transcripts.find(
      (item) => item.id === Number(transcriptId)
    );

    return transcript
      ? getVideoTitle(transcript.video)
      : `Transcript ID: ${transcriptId}`;
  };

  return (
    <div className="page">
      <h1>Transcription</h1>

      <p>
        Manage transcripts and timestamped segments for educational videos.
      </p>

      {error && (
        <p className="error-message">
          🔴 {error}
        </p>
      )}

      {success && (
        <p className="success-message">
          🟢 {success}
        </p>
      )}

      {loading ? (
        <p>Loading transcription data...</p>
      ) : (
        <>
          <div className="topic-form-card">
            <h2>Add Transcript</h2>

            <form onSubmit={saveTranscript}>
              <div className="form-group">
                <label>Video</label>

                <select
                  name="video"
                  value={transcriptForm.video}
                  onChange={handleTranscriptChange}
                  required
                >
                  <option value="">Select a video</option>

                  {videos.map((video) => (
                    <option key={video.id} value={video.id}>
                      {video.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Language</label>

                <select
                  name="language"
                  value={transcriptForm.language}
                  onChange={handleTranscriptChange}
                >
                  <option value="en">English</option>
                  <option value="te">Telugu</option>
                  <option value="hi">Hindi</option>
                </select>
              </div>

              <div className="form-group">
                <label>Transcript Text</label>

                <textarea
                  name="full_text"
                  value={transcriptForm.full_text}
                  onChange={handleTranscriptChange}
                  placeholder="Enter transcript text..."
                  rows={6}
                  required
                />
              </div>

              <button type="submit">Save Transcript</button>
            </form>
          </div>

          <div className="topic-form-card">
            <h2>Create Timestamped Segment</h2>

            <p>
              Select a saved transcript, enter a section of text,
              and specify its start and end times in seconds.
            </p>

            <form onSubmit={saveSegment}>
              <div className="form-group">
                <label>Transcript</label>

                <select
                  name="transcript"
                  value={segmentForm.transcript}
                  onChange={handleSegmentChange}
                  required
                >
                  <option value="">Select a transcript</option>

                  {transcripts.map((transcript) => (
                    <option
                      key={transcript.id}
                      value={transcript.id}
                    >
                      {getVideoTitle(transcript.video)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Segment Text</label>

                <textarea
                  name="text"
                  value={segmentForm.text}
                  onChange={handleSegmentChange}
                  placeholder="Enter the text for this segment..."
                  rows={4}
                  required
                />
              </div>

              <div className="form-group">
                <label>Start Time (seconds)</label>

                <input
                  type="number"
                  name="start_time"
                  value={segmentForm.start_time}
                  onChange={handleSegmentChange}
                  min="0"
                  step="0.1"
                  placeholder="Example: 0"
                  required
                />
              </div>

              <div className="form-group">
                <label>End Time (seconds)</label>

                <input
                  type="number"
                  name="end_time"
                  value={segmentForm.end_time}
                  onChange={handleSegmentChange}
                  min="0.1"
                  step="0.1"
                  placeholder="Example: 15.5"
                  required
                />
              </div>

              <button type="submit">Save Segment</button>
            </form>
          </div>

          <div className="dashboard-section">
            <h2>Saved Transcript Segments</h2>

            {segments.length === 0 ? (
              <div className="empty-state">
                <h3>No segments available</h3>
                <p>Create your first timestamped segment above.</p>
              </div>
            ) : (
              <div className="dashboard-cards">
                {segments.map((segment) => (
                  <div className="card" key={segment.id}>
                    <h3>
                      {getTranscriptTitle(segment.transcript)}
                    </h3>

                    <p>{segment.text}</p>

                    <p>
                      <strong>Start:</strong>{" "}
                      {segment.start_time}s
                    </p>

                    <p>
                      <strong>End:</strong>{" "}
                      {segment.end_time}s
                    </p>

                    <p>
                      <strong>Duration:</strong>{" "}
                      {(
                        segment.end_time - segment.start_time
                      ).toFixed(1)}{" "}
                      seconds
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default Transcription;
