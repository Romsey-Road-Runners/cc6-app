import { render, screen } from '@testing-library/react';
import App from './App';

test('renders navigation links', () => {
  render(<App />);
  expect(screen.getByText('Results')).toBeInTheDocument();
  expect(screen.getByText('Championships')).toBeInTheDocument();
  expect(screen.getByText('Register')).toBeInTheDocument();
});

test('renders dark mode toggle', () => {
  render(<App />);
  expect(screen.getByText('🌙')).toBeInTheDocument();
});
