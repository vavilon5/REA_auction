import client, { setCsrfToken } from './client';
import type { User } from './types';
import axios from 'axios';

export async function fetchCsrf(): Promise<string> {
  const { data } = await axios.get('/api/auth/csrf/', { withCredentials: true });
  setCsrfToken(data.csrfToken);
  return data.csrfToken;
}

export async function login(username: string, password: string): Promise<User> {
  await fetchCsrf();
  const { data } = await client.post<User & { csrfToken: string }>('/auth/login/', {
    username,
    password,
  });
  setCsrfToken(data.csrfToken);
  return data;
}

export async function logout(): Promise<void> {
  await client.post('/auth/logout/');
}

export async function getMe(): Promise<User> {
  const { data } = await client.get<User>('/auth/me/');
  return data;
}
