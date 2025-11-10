import { render, screen } from '@testing-library/react';
import App from './App';

test('renders race results heading', () => {
  render(<App />);
  const heading = screen.getByText(/race results/i);
  expect(heading).toBeInTheDocument();
});
