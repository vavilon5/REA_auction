import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

let csrfToken = '';

export function setCsrfToken(token: string) {
  csrfToken = token;
}

client.interceptors.request.use((config) => {
  if (csrfToken && config.method !== 'get') {
    config.headers['X-CSRFToken'] = csrfToken;
  }
  return config;
});

// On 403 try to refresh CSRF once then retry
client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 403 && !original._csrfRetried) {
      original._csrfRetried = true;
      try {
        const { data } = await axios.get('/api/auth/csrf/', { withCredentials: true });
        setCsrfToken(data.csrfToken);
        original.headers['X-CSRFToken'] = data.csrfToken;
        return client(original);
      } catch {
        // fall through to original error
      }
    }
    return Promise.reject(error);
  },
);

export default client;
