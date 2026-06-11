// Jest setup file — provides manual mocks for testing-library if not installed

// Mock @testing-library/react core functions
const React = require('react');

// Simple render implementation that mounts into a div
function render(ui, options = {}) {
  const container = document.createElement('div');
  document.body.appendChild(container);

  const { container: _container } = options;
  const target = _container || container;

  const cleanup = () => {
    React.unmountComponentAtNode(target);
    if (target.parentNode) target.parentNode.removeChild(target);
  };

  // Use React 18 createRoot if available, else render
  try {
    const root = React.createRoot ? React.createRoot(target) : null;
    if (root) {
      root.render(ui);
    } else {
      React.render(ui, target);
    }
  } catch {
    React.render(ui, target);
  }

  return {
    container: target,
    unmount: cleanup,
    rerender: (newUi) => {
      try {
        const root = React.createRoot ? React.createRoot(target) : null;
        if (root) {
          root.render(newUi);
        } else {
          React.render(newUi, target);
        }
      } catch {
        React.render(newUi, target);
      }
    },
    debug: () => console.log(target.innerHTML),
    cleanup,
    asFragment: () => target.innerHTML,
  };
}

function cleanup() {
  document.body.innerHTML = '';
}

// Query helpers
function screen() {
  return {
    getByText: (text) => {
      const el = document.body.querySelector(`*:not(script):not(style)`);
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
      let node;
      while ((node = walker.nextNode())) {
        if (node.textContent?.includes(text)) {
          return node.parentElement;
        }
      }
      return null;
    },
    getByRole: (role, { name } = {}) => {
      const els = document.body.querySelectorAll(`[role="${role}"]`);
      if (name) {
        for (const el of els) {
          if (el.textContent?.includes(name)) return el;
        }
      }
      return els[0] || null;
    },
    getByTestId: (id) => document.body.querySelector(`[data-testid="${id}"]`),
    queryByText: (text) => {
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
      let node;
      while ((node = walker.nextNode())) {
        if (node.textContent?.includes(text)) {
          return node.parentElement;
        }
      }
      return null;
    },
    queryByTestId: (id) => document.body.querySelector(`[data-testid="${id}"]`),
    findByText: async (text) => screen().getByText(text),
    findByTestId: async (id) => screen().getByTestId(id),
    getByLabelText: (label) => {
      const labels = document.body.querySelectorAll('label');
      for (const lbl of labels) {
        if (lbl.textContent?.includes(label)) {
          const forAttr = lbl.getAttribute('for');
          if (forAttr) return document.getElementById(forAttr);
        }
      }
      return null;
    },
    getByPlaceholderText: (placeholder) => {
      return document.body.querySelector(`[placeholder="${placeholder}"]`);
    },
  };
}

// Fire events
function fireEvent(element, eventName, options = {}) {
  const event = new Event(eventName, { bubbles: true, cancelable: true, ...options });
  element.dispatchEvent(event);
}

fireEvent.click = (element, options) => fireEvent(element, 'click', options);
fireEvent.change = (element, options) => fireEvent(element, 'change', options);
fireEvent.keyDown = (element, options) => fireEvent(element, 'keydown', options);
fireEvent.keyUp = (element, options) => fireEvent(element, 'keyup', options);
fireEvent.focus = (element, options) => fireEvent(element, 'focus', options);
fireEvent.blur = (element, options) => fireEvent(element, 'blur', options);
fireEvent.dragStart = (element, options) => fireEvent(element, 'dragstart', options);
fireEvent.dragOver = (element, options) => fireEvent(element, 'dragover', options);
fireEvent.dragEnter = (element, options) => fireEvent(element, 'dragenter', options);
fireEvent.dragLeave = (element, options) => fireEvent(element, 'dragleave', options);
fireEvent.drop = (element, options) => fireEvent(element, 'drop', options);
fireEvent.submit = (element, options) => {
  if (element.tagName === 'FORM') {
    fireEvent(element, 'submit', options);
  }
};

function waitFor(callback, { timeout = 1000, interval = 50 } = {}) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const check = () => {
      try {
        const result = callback();
        resolve(result);
      } catch (e) {
        if (Date.now() - start > timeout) {
          reject(new Error(`waitFor timed out after ${timeout}ms`));
        } else {
          setTimeout(check, interval);
        }
      }
    };
    check();
  });
}

function act(callback) {
  const result = callback();
  return result;
}

// jest-dom matchers
expect.extend({
  toBeInTheDocument(received) {
    const pass = received !== null && document.body.contains(received);
    return {
      pass,
      message: () =>
        `expected element ${pass ? 'not' : ''} to be in the document`,
    };
  },
  toHaveClass(received, className) {
    const pass = received?.classList?.contains(className);
    return {
      pass,
      message: () =>
        `expected element ${pass ? 'not' : ''} to have class "${className}"`,
    };
  },
  toHaveAttribute(received, attr, value) {
    const actual = received?.getAttribute(attr);
    const pass = value !== undefined ? actual === value : actual !== null;
    return {
      pass,
      message: () =>
        `expected element ${pass ? 'not' : ''} to have attribute "${attr}"${
          value !== undefined ? ` with value "${value}"` : ''
        }`,
    };
  },
  toBeDisabled(received) {
    const pass = received?.disabled === true;
    return {
      pass,
      message: () => `expected element ${pass ? 'not' : ''} to be disabled`,
    };
  },
  toBeEnabled(received) {
    const pass = received?.disabled !== true;
    return {
      pass,
      message: () => `expected element ${pass ? 'not' : ''} to be enabled`,
    };
  },
  toHaveValue(received, value) {
    const pass = received?.value === value;
    return {
      pass,
      message: () =>
        `expected element ${pass ? 'not' : ''} to have value "${value}"`,
    };
  },
  toHaveTextContent(received, text) {
    const pass = received?.textContent?.includes(text);
    return {
      pass,
      message: () =>
        `expected element ${pass ? 'not' : ''} to have text content "${text}"`,
    };
  },
});

// Expose globals
global.render = render;
global.cleanup = cleanup;
global.screen = screen;
global.fireEvent = fireEvent;
global.waitFor = waitFor;
global.act = act;

// Clean up after each test
afterEach(() => {
  cleanup();
});
