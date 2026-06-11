import React from 'react';
import { Button } from '@/components/ui/button';

describe('Button Component', () => {
  it('renders children text', () => {
    const { container } = render(<Button>Click me</Button>);
    expect(container.textContent).toBe('Click me');
  });

  it('renders as button element by default', () => {
    const { container } = render(<Button>Test</Button>);
    const button = container.querySelector('button');
    expect(button).toBeInTheDocument();
    expect(button?.tagName).toBe('BUTTON');
  });

  it('applies default variant classes', () => {
    const { container } = render(<Button>Default</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('bg-primary');
    expect(button).toHaveClass('text-primary-foreground');
  });

  it('applies destructive variant classes', () => {
    const { container } = render(<Button variant="destructive">Delete</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('bg-destructive');
    expect(button).toHaveClass('text-destructive-foreground');
  });

  it('applies outline variant classes', () => {
    const { container } = render(<Button variant="outline">Outline</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('border');
    expect(button).toHaveClass('border-input');
  });

  it('applies secondary variant classes', () => {
    const { container } = render(<Button variant="secondary">Secondary</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('bg-secondary');
  });

  it('applies ghost variant classes', () => {
    const { container } = render(<Button variant="ghost">Ghost</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('hover:bg-accent');
  });

  it('applies link variant classes', () => {
    const { container } = render(<Button variant="link">Link</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('text-primary');
    expect(button).toHaveClass('underline-offset-4');
  });

  it('applies size classes', () => {
    const { container } = render(<Button size="sm">Small</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('h-9');
    expect(button).toHaveClass('rounded-md');
    expect(button).toHaveClass('px-3');
  });

  it('applies lg size classes', () => {
    const { container } = render(<Button size="lg">Large</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('h-11');
    expect(button).toHaveClass('px-8');
  });

  it('applies icon size classes', () => {
    const { container } = render(<Button size="icon">+</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('h-10');
    expect(button).toHaveClass('w-10');
  });

  it('forwards additional className', () => {
    const { container } = render(<Button className="my-custom-class">Custom</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveClass('my-custom-class');
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    const { container } = render(<Button onClick={handleClick}>Click</Button>);
    const button = container.querySelector('button')!;
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('can be disabled', () => {
    const handleClick = jest.fn();
    const { container } = render(<Button disabled onClick={handleClick}>Disabled</Button>);
    const button = container.querySelector('button')!;
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('accepts type attribute', () => {
    const { container } = render(<Button type="submit">Submit</Button>);
    const button = container.querySelector('button');
    expect(button).toHaveAttribute('type', 'submit');
  });

  it('forwards ref', () => {
    const ref = React.createRef<HTMLButtonElement>();
    const { container } = render(<Button ref={ref}>Ref</Button>);
    expect(ref.current).toBe(container.querySelector('button'));
  });
});
