import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080';

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

  // Apply dark mode class to html element for Tailwind
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
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
    <div
      className={`min-h-screen transition-colors duration-300 ${darkMode ? 'dark' : ''}`}
    >
      <nav className="bg-white dark:bg-gray-900 shadow-lg sticky top-0 z-50 transition-colors duration-300">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <div className="flex-shrink-0">
              <img
                src="/cc6-slogan-black.png"
                alt="CC6 Logo"
                className="h-10 w-auto"
              />
            </div>
            <div className="flex items-center space-x-8">
              <a
                href="#results"
                className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors"
              >
                Results
              </a>
              <a
                href="#championships"
                className="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 font-medium transition-colors"
              >
                Championships
              </a>
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
        <div className="max-w-6xl mx-auto px-4 py-8">
          <h1 className="text-4xl font-bold text-center text-gray-900 dark:text-white mb-8">
            Race Results
          </h1>

          <div className="flex flex-wrap justify-center gap-4 mb-8">
            <select
              value={selectedSeason}
              onChange={(e) => setSelectedSeason(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
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
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Genders</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
            </select>

            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Loading results...
              </p>
            </div>
          )}

          {results.length > 0 && (
            <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {selectedRace} Results
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Position
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Gender
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Club
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                    {results.map((result, index) => (
                      <tr
                        key={result.finish_token}
                        className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          {index + 1}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                          {result.participant?.first_name}{' '}
                          {result.participant?.last_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {result.participant?.gender}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {result.participant?.age_category}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {result.participant?.club}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
