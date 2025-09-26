import { render, screen } from '@testing-library/react';
import App from './App';

it('should render the App', () => {
  render(<App />);
  expect(screen.getByText('Shorty+QR')).toBeInTheDocument();
});
