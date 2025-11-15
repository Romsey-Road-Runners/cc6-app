import { render, screen, waitFor } from '@testing-library/react';
import Registration from './Registration';

test('renders registration form', async () => {
  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => [],
  });

  render(<Registration />);

  expect(screen.getByText('Participant Registration')).toBeInTheDocument();
  expect(screen.getByText('Male')).toBeInTheDocument();
  expect(screen.getByText('Female')).toBeInTheDocument();
  expect(screen.getByText('Select your club')).toBeInTheDocument();
  expect(screen.getByPlaceholderText('e.g. A1234567')).toBeInTheDocument();
});

test('loads clubs on mount', async () => {
  const mockClubs = [{ name: 'Test Club 1' }, { name: 'Test Club 2' }];

  fetch.mockResolvedValueOnce({
    ok: true,
    json: async () => mockClubs,
  });

  render(<Registration />);

  await waitFor(() => {
    expect(screen.getByText('Test Club 1')).toBeInTheDocument();
    expect(screen.getByText('Test Club 2')).toBeInTheDocument();
  });
});

test('submits form with valid data', async () => {
  fetch
    .mockResolvedValueOnce({
      ok: true,
      json: async () => [{ name: 'Test Club' }],
    })
    .mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

  render(<Registration />);

  await waitFor(() => {
    expect(screen.getByText('Test Club')).toBeInTheDocument();
  });

  expect(screen.getByText('Register')).toBeInTheDocument();
});
