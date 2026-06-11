import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';

describe('Card Component', () => {
  it('renders Card with children', () => {
    const { container } = render(<Card>Card Content</Card>);
    expect(container.textContent).toBe('Card Content');
  });

  it('Card has correct base classes', () => {
    const { container } = render(<Card>Test</Card>);
    const div = container.querySelector('div');
    expect(div).toHaveClass('rounded-lg');
    expect(div).toHaveClass('border');
    expect(div).toHaveClass('bg-card');
    expect(div).toHaveClass('shadow-sm');
  });

  it('Card forwards className', () => {
    const { container } = render(<Card className="extra-class">Test</Card>);
    const div = container.querySelector('div');
    expect(div).toHaveClass('extra-class');
  });

  it('renders CardHeader with children', () => {
    const { container } = render(<CardHeader><h3>Header</h3></CardHeader>);
    expect(container.querySelector('h3')?.textContent).toBe('Header');
  });

  it('CardHeader has correct classes', () => {
    const { container } = render(<CardHeader>Header</CardHeader>);
    const div = container.querySelector('div');
    expect(div).toHaveClass('flex');
    expect(div).toHaveClass('flex-col');
    expect(div).toHaveClass('p-6');
  });

  it('renders CardTitle', () => {
    const { container } = render(<CardTitle>Title</CardTitle>);
    expect(container.textContent).toBe('Title');
  });

  it('CardTitle has correct classes', () => {
    const { container } = render(<CardTitle>Title</CardTitle>);
    const div = container.querySelector('div');
    expect(div).toHaveClass('text-2xl');
    expect(div).toHaveClass('font-semibold');
  });

  it('renders CardDescription', () => {
    const { container } = render(<CardDescription>Description text</CardDescription>);
    expect(container.textContent).toBe('Description text');
  });

  it('CardDescription has correct classes', () => {
    const { container } = render(<CardDescription>Desc</CardDescription>);
    const div = container.querySelector('div');
    expect(div).toHaveClass('text-sm');
    expect(div).toHaveClass('text-muted-foreground');
  });

  it('renders CardContent with children', () => {
    const { container } = render(<CardContent><p>Content</p></CardContent>);
    expect(container.querySelector('p')?.textContent).toBe('Content');
  });

  it('CardContent has p-6 pt-0', () => {
    const { container } = render(<CardContent>Content</CardContent>);
    const div = container.querySelector('div');
    expect(div).toHaveClass('p-6');
    expect(div).toHaveClass('pt-0');
  });

  it('renders CardFooter', () => {
    const { container } = render(<CardFooter>Footer</CardFooter>);
    expect(container.textContent).toBe('Footer');
  });

  it('CardFooter has correct classes', () => {
    const { container } = render(<CardFooter>Footer</CardFooter>);
    const div = container.querySelector('div');
    expect(div).toHaveClass('flex');
    expect(div).toHaveClass('items-center');
    expect(div).toHaveClass('p-6');
    expect(div).toHaveClass('pt-0');
  });

  it('Card forwards ref', () => {
    const ref = React.createRef<HTMLDivElement>();
    const { container } = render(<Card ref={ref}>Test</Card>);
    expect(ref.current).toBe(container.querySelector('div'));
  });

  it('CardHeader forwards ref', () => {
    const ref = React.createRef<HTMLDivElement>();
    const { container } = render(<CardHeader ref={ref}>Header</CardHeader>);
    expect(ref.current).toBe(container.querySelector('div'));
  });

  it('nested Card components render correctly', () => {
    const { container } = render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Description</CardDescription>
        </CardHeader>
        <CardContent>Content</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>
    );
    expect(container.textContent).toContain('Title');
    expect(container.textContent).toContain('Description');
    expect(container.textContent).toContain('Content');
    expect(container.textContent).toContain('Footer');
  });
});
