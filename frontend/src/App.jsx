import { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import RaceResults from './components/RaceResults';
import Championships from './components/Championships';
import Registration from './components/Registration';
import ParticipantResults from './components/ParticipantResults';
import './App.css';

function App() {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) {
      return JSON.parse(saved);
    }
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  // Apply dark mode class to html element for Tailwind
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  return (
    <Router>
      <div
        className={`min-h-screen transition-colors duration-300 ${darkMode ? 'dark' : ''}`}
      >
        <nav className="bg-white dark:bg-gray-900 shadow-lg sticky top-0 z-50 transition-colors duration-300">
          <div className="max-w-6xl mx-auto px-4">
            <div className="flex justify-between items-center h-16">
              <div className="shrink-0">
                <img
                  src="/cc6-slogan-black.png"
                  alt="CC6 Logo"
                  className="h-10 w-auto"
                />
              </div>
              <div className="flex items-center space-x-8">
                <Link
                  to="/"
                  className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors"
                >
                  Results
                </Link>
                <Link
                  to="/championships"
                  className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors"
                >
                  Championships
                </Link>
                <Link
                  to="/register"
                  className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors"
                >
                  Register
                </Link>
                <button
                  className="p-2 rounded-full border-2 border-current hover:scale-110 transition-transform duration-200"
                  onClick={() => setDarkMode(!darkMode)}
                  aria-label="Toggle dark mode"
                >
                  {darkMode ? '☀️' : '🌙'}
                </button>
              </div>
            </div>
          </div>
        </nav>

        <main className="bg-gray-50 dark:bg-gray-800 min-h-screen transition-colors duration-300">
          <Routes>
            <Route path="/" element={<RaceResults />} />
            <Route path="/championships" element={<Championships />} />
            <Route path="/register" element={<Registration />} />
            <Route
              path="/participant/:participantId"
              element={<ParticipantResults />}
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
