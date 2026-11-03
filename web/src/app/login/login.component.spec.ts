import { afterEach, describe, expect, it, vi } from 'vitest';
import '@angular/compiler';
import type { Router } from '@angular/router';
import axios from 'axios';
import { LoginComponent } from './login.component';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}));

function createStorage() {
  const values = new Map<string, string>();
  return {
    clear: vi.fn(() => values.clear()),
    getItem: vi.fn((key: string) => values.get(key) ?? null),
    key: vi.fn((index: number) => [...values.keys()][index] ?? null),
    removeItem: vi.fn((key: string) => values.delete(key)),
    setItem: vi.fn((key: string, value: string) => values.set(key, value)),
    get length() {
      return values.size;
    }
  } satisfies Storage;
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('LoginComponent service endpoint', () => {
  it('posts the existing login request to the configured endpoint', async () => {
    const storage = createStorage();
    vi.stubGlobal('localStorage', storage);
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'test-token', user: { username: 'student' } }
    } as never);
    const router = {
      navigate: vi.fn().mockResolvedValue(true)
    } as unknown as Router;
    const component = new LoginComponent(router);
    component.username = 'student';
    component.password = 'Workshop123!';

    await component.login();

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'Workshop123!', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(storage.getItem('workshop_token')).toBe('test-token');
    expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
  });
});
