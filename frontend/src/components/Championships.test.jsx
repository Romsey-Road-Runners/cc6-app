import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import Championships from './Championships';

global.fetch = vi.fn();

beforeEach(() => {
  fetch.mockClear();
});

test('renders championships heading', () => {
  fetch.mockResolvedValue({
    ok: true,
    json: async () => ({ seasons: [] }),
  });

  render(<Championships />);
  expect(screen.getByText('Championship Results')).toBeInTheDocument();
});

test('displays team and individual toggle buttons', () => {
  fetch.mockResolvedValue({
    ok: true,
    json: async () => ({ seasons: [] }),
  });

  render(<Championships />);
  expect(screen.getByText('Team')).toBeInTheDocument();
  expect(screen.getByText('Individual')).toBeInTheDocument();
});

test('switches between team and individual championships', async () => {
  fetch.mockResolvedValue({
    ok: true,
    json: async () => ({ seasons: [] }),
  });

  render(<Championships />);

  const individualRadio = screen.getByDisplayValue('individual');
  fireEvent.click(individualRadio);

  expect(individualRadio).toBeChecked();
});

test('displays season selector', () => {
  fetch.mockResolvedValue({
    ok: true,
    json: async () => ({ seasons: [] }),
  });

  render(<Championships />);
  expect(screen.getByText('Season:')).toBeInTheDocument();
});
