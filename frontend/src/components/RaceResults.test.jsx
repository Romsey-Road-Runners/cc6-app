import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import RaceResults from './RaceResults';

// Mock fetch
global.fetch = vi.fn();

beforeEach(() => {
  fetch.mockClear();
});

test('renders race results heading', () => {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ seasons: [] }),
  });

  render(<RaceResults />);
  expect(screen.getByText('Race Results')).toBeInTheDocument();
});

test('displays season selector', () => {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ seasons: [] }),
  });

  render(<RaceResults />);
  expect(screen.getByText('Select Season')).toBeInTheDocument();
});

test('displays seasons after loading', async () => {
  const mockSeasons = [{ name: '2024', races: [{ name: 'Race 1' }] }];

  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => ({ seasons: mockSeasons }),
  });

  render(<RaceResults />);

  await waitFor(() => {
    expect(screen.getByText('Select Season')).toBeInTheDocument();
  });
});
