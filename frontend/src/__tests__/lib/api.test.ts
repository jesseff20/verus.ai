/**
 * Tests for api.ts — Axios instance with CSRF interceptor and 401 redirect
 */

// We'll test the axios configuration by inspecting the instance
// But since axios.create returns a new instance, we mock axios and test
// the interceptor logic

// Store original location for restore
const originalLocation = window.location;

beforeEach(() => {
  // Mock window.location
  delete (window as any).location;
  window.location = { ...originalLocation, href: '' } as any;

  // Mock document.cookie
  Object.defineProperty(document, 'cookie', {
    writable: true,
    value: '',
  });
});

afterEach(() => {
  window.location = originalLocation;
});

describe('API Axios Instance', () => {
  it('creates an axios instance with correct base URL', () => {
    // Re-import to get fresh module
    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;
      expect(axios.create).toHaveBeenCalled();
      const callArgs = (axios.create as jest.Mock).mock.calls[0][0];
      expect(callArgs).toHaveProperty('baseURL');
      expect(callArgs).toHaveProperty('headers.Content-Type', 'application/json');
    });
  });

  it('uses NEXT_PUBLIC_API_URL env var as baseURL', () => {
    const originalEnv = process.env.NEXT_PUBLIC_API_URL;
    process.env.NEXT_PUBLIC_API_URL = 'http://test.api.com';

    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;
      const callArgs = (axios.create as jest.Mock).mock.calls[0][0];
      expect(callArgs.baseURL).toBe('http://test.api.com');
    });

    process.env.NEXT_PUBLIC_API_URL = originalEnv;
  });

  it('falls back to /api/v1 when NEXT_PUBLIC_API_URL is not set', () => {
    const originalEnv = process.env.NEXT_PUBLIC_API_URL;
    delete process.env.NEXT_PUBLIC_API_URL;

    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;
      const callArgs = (axios.create as jest.Mock).mock.calls[0][0];
      expect(callArgs.baseURL).toBe('/api/v1');
    });

    process.env.NEXT_PUBLIC_API_URL = originalEnv;
  });
});

describe('CSRF Interceptor', () => {
  it('adds X-CSRFToken header from cookie', () => {
    document.cookie = 'csrftoken=abc123csrf; path=/';

    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;

      // Get the request interceptor
      const requestInterceptor = (axios.interceptors.request.use as jest.Mock).mock.calls[0][0];

      const config = { headers: {} };
      const result = requestInterceptor(config);

      expect(result.headers['X-CSRFToken']).toBe('abc123csrf');
    });
  });

  it('does not add CSRF header when cookie is missing', () => {
    document.cookie = '';

    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;

      const requestInterceptor = (axios.interceptors.request.use as jest.Mock).mock.calls[0][0];
      const config = { headers: {} };
      const result = requestInterceptor(config);

      expect(result.headers['X-CSRFToken']).toBeUndefined();
    });
  });

  it('preserves existing headers', () => {
    document.cookie = 'csrftoken=abc123';

    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;

      const requestInterceptor = (axios.interceptors.request.use as jest.Mock).mock.calls[0][0];
      const config = { headers: { 'Authorization': 'Bearer token123' } };
      const result = requestInterceptor(config);

      expect(result.headers['Authorization']).toBe('Bearer token123');
      expect(result.headers['X-CSRFToken']).toBe('abc123');
    });
  });
});

describe('401 Redirect Interceptor', () => {
  it('redirects to /login on 401 response', () => {
    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;

      // Get the response error interceptor
      const responseInterceptor = (axios.interceptors.response.use as jest.Mock).mock.calls[0][1];

      const error = {
        response: { status: 401 },
      };

      expect.assertions(1);
      return responseInterceptor(error).catch(() => {
        expect(window.location.href).toBe('/login');
      });
    });
  });

  it('does not redirect on non-401 errors', () => {
    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;

      const responseInterceptor = (axios.interceptors.response.use as jest.Mock).mock.calls[0][1];

      const error = {
        response: { status: 403 },
      };

      expect.assertions(1);
      return responseInterceptor(error).catch(() => {
        expect(window.location.href).not.toBe('/login');
      });
    });
  });

  it('does not redirect on 500 errors', () => {
    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;

      const responseInterceptor = (axios.interceptors.response.use as jest.Mock).mock.calls[0][1];

      const error = {
        response: { status: 500 },
      };

      expect.assertions(1);
      return responseInterceptor(error).catch(() => {
        expect(window.location.href).not.toBe('/login');
      });
    });
  });

  it('rejects the promise after 401 redirect', () => {
    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;

      const responseInterceptor = (axios.interceptors.response.use as jest.Mock).mock.calls[0][1];

      const error = { response: { status: 401 } };

      expect.assertions(1);
      return expect(responseInterceptor(error)).rejects.toEqual(error);
    });
  });

  it('passes through successful responses', () => {
    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;

      const responseInterceptor = (axios.interceptors.response.use as jest.Mock).mock.calls[0][0];

      const response = { data: { success: true }, status: 200 };
      const result = responseInterceptor(response);

      expect(result).toEqual(response);
    });
  });

  it('handles network errors without response object', () => {
    jest.isolateModules(() => {
      const axios = require('axios');
      const api = require('@/lib/api').default;

      const responseInterceptor = (axios.interceptors.response.use as jest.Mock).mock.calls[0][1];

      const error = new Error('Network Error');

      expect.assertions(1);
      return responseInterceptor(error).catch((err: Error) => {
        expect(err.message).toBe('Network Error');
      });
    });
  });
});

describe('API Module Export', () => {
  it('exports default instance', () => {
    jest.isolateModules(() => {
      const api = require('@/lib/api').default;
      expect(api).toBeDefined();
      expect(typeof api.get).toBe('function');
      expect(typeof api.post).toBe('function');
      expect(typeof api.put).toBe('function');
      expect(typeof api.patch).toBe('function');
      expect(typeof api.delete).toBe('function');
    });
  });

  it('adds both request and response interceptors', () => {
    jest.isolateModules(() => {
      const axios = require('axios');
      require('@/lib/api');
      expect(axios.interceptors.request.use).toHaveBeenCalledTimes(1);
      expect(axios.interceptors.response.use).toHaveBeenCalledTimes(1);
    });
  });
});
