import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8080';

function App() {
  const [seasons, setSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState('');
  const [races, setRaces] = useState([]);
  const [selectedRace, setSelectedRace] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedGender, setSelectedGender] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    if (saved !== null) {
      return JSON.parse(saved);
    }
    // Fallback for test environment
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false; // Default to light mode in test environment
  });

  // Apply dark mode class to body
  useEffect(() => {
    document.body.className = darkMode ? 'dark-mode' : '';
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  // Load seasons on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/seasons`)
      .then((res) => res.json())
      .then((data) => {
        setSeasons(data.seasons);
        if (data.default_season) {
          setSelectedSeason(data.default_season);
        }
        // Auto-select default race if available
        if (data.default_race && data.default_season) {
          setSelectedRace(data.default_race);
        }
      });
  }, []);

  // Load races when season changes
  useEffect(() => {
    if (selectedSeason) {
      fetch(`${API_BASE}/api/seasons/${selectedSeason}`)
        .then((res) => res.json())
        .then((data) => {
          setRaces(data.races || []);
          // Only clear race selection if manually changing season
          if (!selectedRace) {
            setResults([]);
          }
          // Generate age categories
          const categorySize = data.age_category_size || 5;
          const cats = ['Senior'];
          for (let age = 40; age <= 80; age += categorySize) {
            cats.push(`V${age}`);
          }
          setCategories(cats);
        });
    }
  }, [selectedSeason, selectedRace]);

  // Load results when race or filters change
  useEffect(() => {
    if (selectedSeason && selectedRace) {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedGender) params.append('gender', selectedGender);
      if (selectedCategory) params.append('category', selectedCategory);

      const url = `${API_BASE}/api/races/${selectedSeason}/${selectedRace}${params.toString() ? '?' + params.toString() : ''}`;

      fetch(url)
        .then((res) => res.json())
        .then((data) => {
          setResults(data.results || []);
          setLoading(false);
        });
    }
  }, [selectedSeason, selectedRace, selectedGender, selectedCategory]);

  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-container">
          <div className="nav-logo">
            <img src="/cc6-slogan-black.png" alt="CC6 Logo" className="logo" />
          </div>
          <div className="nav-menu">
            <a href="#results" className="nav-link">
              Results
            </a>
            <a href="#championships" className="nav-link">
              Championships
            </a>
            <button
              className="theme-toggle"
              onClick={() => setDarkMode(!darkMode)}
              aria-label="Toggle dark mode"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </nav>

      <main className="main-content">
        <h1>Race Results</h1>

        <div className="filters">
          <select
            value={selectedSeason}
            onChange={(e) => setSelectedSeason(e.target.value)}
          >
            <option value="">Select Season</option>
            {seasons.map((season) => (
              <option key={season} value={season}>
                {season}
              </option>
            ))}
          </select>

          <select
            value={selectedRace}
            onChange={(e) => setSelectedRace(e.target.value)}
            disabled={!races.length}
          >
            <option value="">Select Race</option>
            {races.map((race) => (
              <option key={race.name} value={race.name}>
                {race.name} ({race.date})
              </option>
            ))}
          </select>

          <select
            value={selectedGender}
            onChange={(e) => setSelectedGender(e.target.value)}
          >
            <option value="">All Genders</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        {loading && <p>Loading results...</p>}

        {results.length > 0 && (
          <div className="results">
            <h2>{selectedRace} Results</h2>
            <table>
              <thead>
                <tr>
                  <th>Position</th>
                  <th>Name</th>
                  <th>Gender</th>
                  <th>Category</th>
                  <th>Club</th>
                </tr>
              </thead>
              <tbody>
                {results.map((result, index) => (
                  <tr key={result.finish_token}>
                    <td>{index + 1}</td>
                    <td>
                      {result.participant?.first_name}{' '}
                      {result.participant?.last_name}
                    </td>
                    <td>{result.participant?.gender}</td>
                    <td>{result.participant?.age_category}</td>
                    <td>{result.participant?.club}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
