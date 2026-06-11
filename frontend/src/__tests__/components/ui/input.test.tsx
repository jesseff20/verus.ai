import React from 'react';
import { Input } from '@/components/ui/input';

describe('Input Component', () => {
  it('renders an input element', () => {
    const { container } = render(<Input />);
    const input = container.querySelector('input');
    expect(input).toBeInTheDocument();
    expect(input?.tagName).toBe('INPUT');
  });

  it('applies base classes', () => {
    const { container } = render(<Input />);
    const input = container.querySelector('input');
    expect(input).toHaveClass('flex');
    expect(input).toHaveClass('h-10');
    expect(input).toHaveClass('w-full');
    expect(input).toHaveClass('rounded-md');
    expect(input).toHaveClass('border');
    expect(input).toHaveClass('border-input');
    expect(input).toHaveClass('bg-background');
    expect(input).toHaveClass('px-3');
    expect(input).toHaveClass('py-2');
    expect(input).toHaveClass('text-sm');
  });

  it('accepts type attribute', () => {
    const { container } = render(<Input type="email" />);
    const input = container.querySelector('input');
    expect(input).toHaveAttribute('type', 'email');
  });

  it('accepts placeholder', () => {
    const { container } = render(<Input placeholder="Enter name" />);
    const input = container.querySelector('input');
    expect(input).toHaveAttribute('placeholder', 'Enter name');
  });

  it('forwards additional className', () => {
    const { container } = render(<Input className="extra-class" />);
    const input = container.querySelector('input');
    expect(input).toHaveClass('extra-class');
  });

  it('handles value changes', () => {
    const handleChange = jest.fn();
    const { container } = render(<Input onChange={handleChange} />);
    const input = container.querySelector('input')!;
    fireEvent.change(input, { target: { value: 'new value' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('supports disabled state', () => {
    const { container } = render(<Input disabled />);
    const input = container.querySelector('input');
    expect(input).toBeDisabled();
  });

  it('displays the correct value', () => {
    const { container } = render(<Input value="test value" readOnly />);
    const input = container.querySelector('input')!;
    expect(input).toHaveValue('test value');
  });

  it('forwards ref', () => {
    const ref = React.createRef<HTMLInputElement>();
    const { container } = render(<Input ref={ref} />);
    expect(ref.current).toBe(container.querySelector('input'));
  });

  it('supports autoFocus', () => {
    const { container } = render(<Input autoFocus />);
    const input = container.querySelector('input');
    expect(document.activeElement).toBe(input);
  });

  it('supports name attribute', () => {
    const { container } = render(<Input name="username" />);
    const input = container.querySelector('input');
    expect(input).toHaveAttribute('name', 'username');
  });

  it('supports required attribute', () => {
    const { container } = render(<Input required />);
    const input = container.querySelector('input');
    expect(input).toHaveAttribute('required');
  });

  it('handles focus and blur events', () => {
    const handleFocus = jest.fn();
    const handleBlur = jest.fn();
    const { container } = render(<Input onFocus={handleFocus} onBlur={handleBlur} />);
    const input = container.querySelector('input')!;
    fireEvent.focus(input);
    expect(handleFocus).toHaveBeenCalledTimes(1);
    fireEvent.blur(input);
    expect(handleBlur).toHaveBeenCalledTimes(1);
  });

  it('handles key down events', () => {
    const handleKeyDown = jest.fn();
    const { container } = render(<Input onKeyDown={handleKeyDown} />);
    const input = container.querySelector('input')!;
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(handleKeyDown).toHaveBeenCalledTimes(1);
  });
});
