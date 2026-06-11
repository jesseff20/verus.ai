'use client';

import * as React from 'react';

const CollapsibleContext = React.createContext<{
  isOpen: boolean;
  toggle: () => void;
}>({ isOpen: false, toggle: () => {} });

interface CollapsibleProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
  className?: string;
}

function Collapsible({ open, onOpenChange, children, className }: CollapsibleProps) {
  const [isOpen, setIsOpen] = React.useState(open ?? false);

  React.useEffect(() => {
    if (open !== undefined) setIsOpen(open);
  }, [open]);

  const toggle = React.useCallback(() => {
    const next = !isOpen;
    setIsOpen(next);
    onOpenChange?.(next);
  }, [isOpen, onOpenChange]);

  return (
    <CollapsibleContext.Provider value={{ isOpen, toggle }}>
      <div className={className} data-state={isOpen ? 'open' : 'closed'}>
        {children}
      </div>
    </CollapsibleContext.Provider>
  );
}

interface CollapsibleTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
}

const CollapsibleTrigger = React.forwardRef<HTMLButtonElement, CollapsibleTriggerProps>(
  ({ children, asChild, onClick, ...props }, ref) => {
    const { toggle } = React.useContext(CollapsibleContext);

    const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
      toggle();
      onClick?.(e);
    };

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as React.ReactElement<Record<string, unknown>>, {
        onClick: (e: React.MouseEvent<HTMLButtonElement>) => {
          toggle();
          const childOnClick = (children as React.ReactElement<Record<string, unknown>>).props.onClick;
          if (typeof childOnClick === 'function') childOnClick(e);
        },
      });
    }

    return (
      <button type="button" ref={ref} onClick={handleClick} {...props}>
        {children}
      </button>
    );
  }
);
CollapsibleTrigger.displayName = 'CollapsibleTrigger';

function CollapsibleContent({ children, className }: { children: React.ReactNode; className?: string }) {
  const { isOpen } = React.useContext(CollapsibleContext);
  if (!isOpen) return null;
  return <div className={className}>{children}</div>;
}

export { Collapsible, CollapsibleTrigger, CollapsibleContent };
