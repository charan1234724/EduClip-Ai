
import { useEffect, useMemo, useState } from "react";
import api from "../services/api";

const initialFormData = {
  title: "",
  category: "",
  keywords: "",
  difficulty: "Beginner",
  trend_score: "",
};

function Topics() {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [formData, setFormData] = useState(initialFormData);

  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [difficultyFilter, setDifficultyFilter] = useState("All");
  const [sortOrder, setSortOrder] = useState("highest");

  const fetchTopics = async () => {
    try {
      const response = await api.get("/api/topics/");
      setTopics(response.data.topics);
      setError("");
    } catch (err) {
      console.error(err);
      setError("Unable to load topics from the backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTopics();
  }, []);

  const categories = useMemo(
    () => [...new Set(topics.map((topic) => topic.category))].sort(),
    [topics]
  );
  
  const topicStats = useMemo(() => {
    const total = topics.length;

    const averageScore =
      total > 0
        ? (
            topics.reduce(
              (sum, topic) => sum + Number(topic.trend_score || 0),
              0
            ) / total
          ).toFixed(1)
        : "0.0";

    const beginner = topics.filter(
      (topic) => topic.difficulty === "Beginner"
    ).length;

    const intermediate = topics.filter(
      (topic) => topic.difficulty === "Intermediate"
    ).length;

    const advanced = topics.filter(
      (topic) => topic.difficulty === "Advanced"
    ).length;

    return {
      averageScore,
      beginner,
      intermediate,
      advanced,
    };
  }, [topics]);


  const filteredTopics = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return topics
      .filter((topic) => {
        const matchesSearch =
          topic.title.toLowerCase().includes(normalizedSearch) ||
          (topic.keywords || []).some((keyword) =>
            keyword.toLowerCase().includes(normalizedSearch)
          );

        const matchesCategory =
          categoryFilter === "All" ||
          topic.category === categoryFilter;

        const matchesDifficulty =
          difficultyFilter === "All" ||
          topic.difficulty === difficultyFilter;

        return (
          matchesSearch &&
          matchesCategory &&
          matchesDifficulty
        );
      })
      .sort((a, b) =>
        sortOrder === "highest"
          ? b.trend_score - a.trend_score
          : a.trend_score - b.trend_score
      );
  }, [
    topics,
    search,
    categoryFilter,
    difficultyFilter,
    sortOrder,
  ]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    try {
      const newTopic = {
        title: formData.title.trim(),
        category: formData.category.trim(),
        keywords: formData.keywords
          .split(",")
          .map((keyword) => keyword.trim())
          .filter(Boolean),
        difficulty: formData.difficulty,
        trend_score: Number(formData.trend_score),
      };

      await api.post("/api/topics/", newTopic);

      setFormData({ ...initialFormData });
      setSuccess("Topic created successfully.");
      await fetchTopics();
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.errors
          ? JSON.stringify(err.response.data.errors)
          : "Unable to create the topic."
      );
    }
  };

  const handleGenerateTopics = async () => {
    const confirmed = window.confirm(
      "Generate 100 topics using AI? This may take some time."
    );

    if (!confirmed) return;

    setGenerating(true);
    setError("");
    setSuccess("");

    try {
      const response = await api.post("/api/topics/generate/", {});

      await fetchTopics();

      
      setSuccess(
        `Generation completed: ${response.data.generated_count ?? 100} topics generated, ` +
        `${response.data.created_count ?? 0} newly created, ` +
        `${response.data.updated_count ?? 0} updated. ` +
        `Database total: ${response.data.total_topics_in_database ?? "refreshed"}.`
      );

  } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.message ||
          "Unable to generate topics. Check the backend and OpenRouter."
      );
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="page">
      <h1>Trending Topics</h1>
      <p>
        Generate, search, and manage educational topics for EduClip AI.
        Trend scores are AI estimates, not verified live popularity.
      </p>

      <div className="topic-form-card">
        <h2>AI Topic Generation</h2>
        <p>
          Generate a fresh batch of 100 educational topic suggestions.
        </p>
        <button
          type="button"
          onClick={handleGenerateTopics}
          disabled={generating}
        >
          {generating ? "Generating topics..." : "Generate 100 Topics"}
        </button>
      </div>

      {success && <p className="success-message">{success}</p>}
      {error && <p className="error-message">🔴 {error}</p>}

      
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-label">Total Topics</span>
          <strong className="stat-value">{topics.length}</strong>
          <span className="stat-description">Topics loaded from the API</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Categories</span>
          <strong className="stat-value">{categories.length}</strong>
          <span className="stat-description">Distinct subject areas</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Average Estimated Score</span>
          <strong className="stat-value">{topicStats.averageScore}</strong>
          <span className="stat-description">Out of 100; not live trend data</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Beginner</span>
          <strong className="stat-value">{topicStats.beginner}</strong>
          <span className="stat-description">Beginner-level topics</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Intermediate</span>
          <strong className="stat-value">{topicStats.intermediate}</strong>
          <span className="stat-description">Intermediate-level topics</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Advanced</span>
          <strong className="stat-value">{topicStats.advanced}</strong>
          <span className="stat-description">Advanced-level topics</span>
        </div>

        <div className="stat-card">
          <span className="stat-label">Filtered Results</span>
          <strong className="stat-value">{filteredTopics.length}</strong>
          <span className="stat-description">Topics matching your filters</span>
        </div>
      </div>


      <div className="topic-form-card">
        <h2>Create Topic Manually</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="topic-title">Topic Title</label>
            <input
              id="topic-title"
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="Example: How Artificial Intelligence Works"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="topic-category">Category</label>
            <input
              id="topic-category"
              type="text"
              name="category"
              value={formData.category}
              onChange={handleChange}
              placeholder="Example: Artificial Intelligence"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="topic-keywords">Keywords</label>
            <input
              id="topic-keywords"
              type="text"
              name="keywords"
              value={formData.keywords}
              onChange={handleChange}
              placeholder="AI, Machine Learning, Technology"
            />
            <small>Separate keywords using commas.</small>
          </div>

          <div className="form-group">
            <label htmlFor="topic-difficulty">Difficulty</label>
            <select
              id="topic-difficulty"
              name="difficulty"
              value={formData.difficulty}
              onChange={handleChange}
            >
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="topic-trend-score">
              Estimated Trend Score (1–100)
            </label>
            <input
              id="topic-trend-score"
              type="number"
              name="trend_score"
              value={formData.trend_score}
              onChange={handleChange}
              placeholder="Example: 90"
              min="1"
              max="100"
              required
            />
          </div>

          <button type="submit">Create Topic</button>
        </form>
      </div>

      <div className="topic-form-card">
        <h2>Explore Topics</h2>

        <div className="form-group">
          <label htmlFor="topic-search">Search title or keywords</label>
          <input
            id="topic-search"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search topics..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="topic-category-filter">Category</label>
          <select
            id="topic-category-filter"
            value={categoryFilter}
            onChange={(event) => setCategoryFilter(event.target.value)}
          >
            <option value="All">All categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="topic-difficulty-filter">Difficulty</label>
          <select
            id="topic-difficulty-filter"
            value={difficultyFilter}
            onChange={(event) => setDifficultyFilter(event.target.value)}
          >
            <option value="All">All levels</option>
            <option value="Beginner">Beginner</option>
            <option value="Intermediate">Intermediate</option>
            <option value="Advanced">Advanced</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="topic-sort">Sort by estimated score</label>
          <select
            id="topic-sort"
            value={sortOrder}
            onChange={(event) => setSortOrder(event.target.value)}
          >
            <option value="highest">Highest first</option>
            <option value="lowest">Lowest first</option>
          </select>
        </div>
      </div>

      {loading && <p>Loading topics...</p>}

      {!loading && filteredTopics.length === 0 && (
        <div className="empty-state">
          <h3>No matching topics</h3>
          <p>Try changing your search or filters.</p>
        </div>
      )}

      
      {!loading && filteredTopics.length > 0 && (
        <div className="dashboard-cards">
          {filteredTopics.map((topic) => {
            const score = Math.max(
              0,
              Math.min(100, Number(topic.trend_score) || 0)
            );

            return (
              <div className="card" key={topic.id}>
                <h3>{topic.title}</h3>

                <p>
                  <strong>Category:</strong> {topic.category}
                </p>

                <p>
                  <strong>Difficulty:</strong>{" "}
                  <span className={`difficulty-badge difficulty-${topic.difficulty.toLowerCase()}`}>
                    {topic.difficulty}
                  </span>
                </p>

                <div className="topic-score">
                  <div className="topic-score-header">
                    <strong>Estimated Trend Score</strong>
                    <span>{score}/100</span>
                  </div>

                  <div
                    className="topic-score-track"
                    role="progressbar"
                    aria-label={`Estimated trend score for ${topic.title}`}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={score}
                  >
                    <div
                      className="topic-score-fill"
                      style={{ width: `${score}%` }}
                    />
                  </div>

                  <small>
                    AI estimate, not verified live popularity.
                  </small>
                </div>

                {topic.keywords?.length > 0 && (
                  <p>
                    <strong>Keywords:</strong>{" "}
                    {topic.keywords.join(", ")}
                  </p>
                )}

                <button
                  type="button"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(topic.title);
                      setSuccess("Topic title copied to clipboard.");
                      setError("");
                    } catch (err) {
                      console.error(err);
                      setError(
                        "Unable to copy the title. Select and copy it manually."
                      );
                    }
                  }}
                >
                  Copy Topic Title
                </button>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}

export default Topics;
