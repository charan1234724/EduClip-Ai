import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";
import LicensedMedia from "./pages/LicensedMedia";
import Dashboard from "./pages/Dashboard";
import Topics from "./pages/Topics";
import Videos from "./pages/Videos";
import Transcription from "./pages/Transcription";
import ClipCreator from "./pages/ClipCreator";
import GeneratedClips from "./pages/GeneratedClips";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">

        <aside className="sidebar">
          <div className="logo">
            <h2>EduClip AI</h2>
            <span>Video Content Curator</span>
          </div>

          <nav className="navigation">
            <Link to="/">Dashboard</Link>

            <Link to="/topics">
              Trending Topics
            </Link>

            <Link to="/videos">
              Video Discovery
            </Link>

            <Link to="/transcription">
              Transcription
            </Link>

            <Link to="/clip-creator">
              Clip Creator
            </Link>

            <Link to="/generated-clips">
              Generated Clips
            </Link>
            <Link to="/licensed-media">Licensed Media</Link>
          </nav>
        </aside>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />

            <Route
              path="/topics"
              element={<Topics />}
            />
            <Route
              path="/licensed-media"
              element={<LicensedMedia />}
            />

            <Route
              path="/videos"
              element={<Videos />}
            />

            <Route
              path="/transcription"
              element={<Transcription />}
            />

            <Route
              path="/clip-creator"
              element={<ClipCreator />}
            />

            <Route
              path="/generated-clips"
              element={<GeneratedClips />}
            />

            <Route
              path="*"
              element={<Navigate to="/" replace />}
            />
          </Routes>
        </main>

      </div>
    </BrowserRouter>
  );
}

export default App;