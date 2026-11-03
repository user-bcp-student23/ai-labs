import { describe, expect, it } from 'vitest';
import { createServiceEndpoints, serviceEndpoints } from './service-endpoints';

describe('service endpoints', () => {
  it('preserves the development service origins and protected paths', () => {
    expect(serviceEndpoints).toEqual({
      login: 'http://localhost:8080/auth/login',
      tasks: 'http://localhost:8000/api/tasks'
    });
  });

  it('uses configured origins without changing the protected paths', () => {
    expect(createServiceEndpoints({
      authServiceOrigin: 'https://auth.example.invalid',
      apiServiceOrigin: 'https://api.example.invalid'
    })).toEqual({
      login: 'https://auth.example.invalid/auth/login',
      tasks: 'https://api.example.invalid/api/tasks'
    });
  });

  it('normalizes origins with a trailing slash', () => {
    expect(createServiceEndpoints({
      authServiceOrigin: 'https://auth.example.invalid/',
      apiServiceOrigin: 'https://api.example.invalid/'
    })).toEqual({
      login: 'https://auth.example.invalid/auth/login',
      tasks: 'https://api.example.invalid/api/tasks'
    });
  });
});
