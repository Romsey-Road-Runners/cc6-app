import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080';

function Championships() {
  const [seasons, setSeasons] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState('');
  const [selectedGender, setSelectedGender] = useState('Male');
  const [championshipType, setChampionshipType] = useState('team');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);
  const [championshipData, setChampionshipData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Load seasons on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/seasons`)
      .then((res) => res.json())
      .then((data) => {
        setSeasons(data.seasons);
        if (data.default_season) {
          setSelectedSeason(data.default_season);
        }
      });
  }, []);

  // Load season data for categories
  useEffect(() => {
    if (selectedSeason) {
      fetch(`${API_BASE}/api/seasons/${selectedSeason}`)
        .then((res) => res.json())
        .then((data) => {
          const categorySize = data.age_category_size || 5;
          const cats = ['Senior'];
          for (let age = 40; age <= 80; age += categorySize) {
            cats.push(`V${age}`);
          }
          setCategories(cats);
        });
    }
  }, [selectedSeason]);

  // Load championship results
  const loadChampionship = () => {
    if (!selectedSeason || !selectedGender) return;

    setLoading(true);
    let endpoint =
      championshipType === 'team'
        ? `${API_BASE}/api/seasons/${selectedSeason}/championship/${selectedGender}`
        : `${API_BASE}/api/seasons/${selectedSeason}/championship/individual`;

    const params = new URLSearchParams();
    if (championshipType === 'individual') {
      params.append('gender', selectedGender);
    }
    if (championshipType === 'individual' && selectedCategory) {
      params.append('category', selectedCategory);
    }
    if (params.toString()) {
      endpoint += `?${params.toString()}`;
    }

    fetch(endpoint)
      .then((res) => res.json())
      .then((data) => {
        setChampionshipData(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Error fetching championship data:', error);
        setLoading(false);
      });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center text-gray-900 dark:text-white mb-8">
        Championship Results
      </h1>

      <div className="space-y-6 mb-8">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Season:
          </label>
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
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Championship Type:
          </label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="type"
                value="team"
                checked={championshipType === 'team'}
                onChange={(e) => setChampionshipType(e.target.value)}
                className="mr-2"
              />
              Team
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="type"
                value="individual"
                checked={championshipType === 'individual'}
                onChange={(e) => setChampionshipType(e.target.value)}
                className="mr-2"
              />
              Individual
            </label>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Gender:
          </label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="gender"
                value="Male"
                checked={selectedGender === 'Male'}
                onChange={(e) => setSelectedGender(e.target.value)}
                className="mr-2"
              />
              Men
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="gender"
                value="Female"
                checked={selectedGender === 'Female'}
                onChange={(e) => setSelectedGender(e.target.value)}
                className="mr-2"
              />
              Women
            </label>
          </div>
        </div>

        {championshipType === 'individual' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Age Category:
            </label>
            <div className="flex gap-4 flex-wrap">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="category"
                  value=""
                  checked={selectedCategory === ''}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="mr-2"
                />
                All Categories
              </label>
              {categories.map((cat) => (
                <label key={cat} className="flex items-center">
                  <input
                    type="radio"
                    name="category"
                    value={cat}
                    checked={selectedCategory === cat}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="mr-2"
                  />
                  {cat}
                </label>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={loadChampionship}
          disabled={!selectedSeason || !selectedGender}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          Load Championship
        </button>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Loading results...
          </p>
        </div>
      )}

      {championshipData && (
        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
              {championshipData.championship_name} - {championshipData.season}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <strong>Scoring:</strong>{' '}
              {championshipData.championship_type === 'individual'
                ? `Best ${championshipData.best_of || 3} race results per individual`
                : `Top ${championshipData.gender === 'Male' ? '4' : '3'} finishers per club per race`}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              <strong>Races included:</strong>{' '}
              {championshipData.championship_type === 'individual'
                ? championshipData.races?.length || 0
                : championshipData.races?.filter((race) =>
                    championshipData.standings?.some((entry) => {
                      const raceData = entry.race_points?.[race.name];
                      return (
                        raceData &&
                        raceData !== '-' &&
                        typeof raceData === 'object' &&
                        raceData.rank
                      );
                    })
                  ).length || 0}
            </p>
            {championshipData.championship_type !== 'individual' && (
              <>
                <p className="text-sm text-gray-600 dark:text-gray-400 italic mt-2">
                  <strong>Note:</strong> Clubs may be marked as disqualified
                  (DQ) due to having insufficient runners in a race.
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 italic">
                  <strong>Note:</strong> The Total Rankings column will be
                  adjusted if a club did not organise a race (for example due to
                  cancellation or if the season is ongoing).
                </p>
              </>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Position
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    {championshipData.championship_type === 'individual'
                      ? 'Name'
                      : 'Club'}
                  </th>
                  {championshipData.championship_type === 'individual' && (
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Category
                    </th>
                  )}
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Total Rankings
                  </th>
                  {championshipData.races?.map((race) => (
                    <th
                      key={race.name}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                    >
                      {race.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {championshipData.standings?.map((entry, index) => {
                  let position = index + 1;
                  return (
                    <tr
                      key={entry.participant_id || entry.name}
                      className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {position}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {championshipData.championship_type === 'individual' &&
                        entry.club
                          ? `${entry.name} (${entry.club})`
                          : entry.name}
                      </td>
                      {championshipData.championship_type === 'individual' && (
                        <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {entry.age_category || '-'}
                        </td>
                      )}
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-bold text-gray-900 dark:text-white">
                        {entry.total_points}
                      </td>
                      {championshipData.races?.map((race) => {
                        if (
                          championshipData.championship_type === 'individual'
                        ) {
                          const position = entry.race_positions?.[race.name];
                          return (
                            <td
                              key={race.name}
                              className="px-4 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"
                            >
                              {position || '-'}
                            </td>
                          );
                        } else {
                          const raceData = entry.race_points?.[race.name];
                          if (raceData === 'ORG' || raceData === 'DQ') {
                            return (
                              <td
                                key={race.name}
                                className="px-4 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"
                              >
                                {raceData}
                              </td>
                            );
                          } else if (raceData?.rank) {
                            const positions = raceData.positions?.join(', ');
                            return (
                              <td
                                key={race.name}
                                className="px-4 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"
                              >
                                {raceData.rank} ({positions} = {raceData.points}{' '}
                                points)
                              </td>
                            );
                          } else {
                            return (
                              <td
                                key={race.name}
                                className="px-4 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"
                              >
                                -
                              </td>
                            );
                          }
                        }
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Championships;
