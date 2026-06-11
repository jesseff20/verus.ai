import React from 'react';
import { Badge } from '@/components/ui/badge';

describe('Badge Component', () => {
  it('renders children text', () => {
    const { container } = render(<Badge>Active</Badge>);
    expect(container.textContent).toBe('Active');
  });

  it('renders as a div element', () => {
    const { container } = render(<Badge>Test</Badge>);
    const el = container.querySelector('div');
    expect(el).toBeInTheDocument();
    expect(el?.tagName).toBe('DIV');
  });

  it('applies base classes', () => {
    const { container } = render(<Badge>Base</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveClass('inline-flex');
    expect(el).toHaveClass('items-center');
    expect(el).toHaveClass('rounded-full');
    expect(el).toHaveClass('px-2.5');
    expect(el).toHaveClass('py-0.5');
    expect(el).toHaveClass('text-xs');
    expect(el).toHaveClass('font-semibold');
  });

  it('applies default variant classes', () => {
    const { container } = render(<Badge>Default</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveClass('bg-primary');
    expect(el).toHaveClass('text-primary-foreground');
  });

  it('applies secondary variant classes', () => {
    const { container } = render(<Badge variant="secondary">Secondary</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveClass('bg-secondary');
    expect(el).toHaveClass('text-secondary-foreground');
  });

  it('applies destructive variant classes', () => {
    const { container } = render(<Badge variant="destructive">Destructive</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveClass('bg-destructive');
    expect(el).toHaveClass('text-destructive-foreground');
  });

  it('applies outline variant classes', () => {
    const { container } = render(<Badge variant="outline">Outline</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveClass('text-foreground');
  });

  it('applies success variant classes', () => {
    const { container } = render(<Badge variant="success">Success</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveClass('bg-green-100');
    expect(el).toHaveClass('text-green-800');
  });

  it('applies warning variant classes', () => {
    const { container } = render(<Badge variant="warning">Warning</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveClass('bg-yellow-100');
    expect(el).toHaveClass('text-yellow-800');
  });

  it('applies info variant classes', () => {
    const { container } = render(<Badge variant="info">Info</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveClass('bg-blue-100');
    expect(el).toHaveClass('text-blue-800');
  });

  it('forwards additional className', () => {
    const { container } = render(<Badge className="custom-badge">Custom</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveClass('custom-badge');
  });

  it('forwards additional HTML attributes', () => {
    const { container } = render(<Badge data-testid="test-badge" id="my-badge">Test</Badge>);
    const el = container.querySelector('div');
    expect(el).toHaveAttribute('data-testid', 'test-badge');
    expect(el).toHaveAttribute('id', 'my-badge');
  });

  it('accepts onClick events', () => {
    const handleClick = jest.fn();
    const { container } = render(<Badge onClick={handleClick}>Clickable</Badge>);
    const el = container.querySelector('div')!;
    fireEvent.click(el);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
