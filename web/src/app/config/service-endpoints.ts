import { environment } from '../../environments/environment';

export interface ServiceOrigins {
  authServiceOrigin: string;
  apiServiceOrigin: string;
}

export function createServiceEndpoints(origins: ServiceOrigins) {
  return {
    login: new URL('/auth/login', origins.authServiceOrigin).toString(),
    tasks: new URL('/api/tasks', origins.apiServiceOrigin).toString()
  };
}

export const serviceEndpoints = createServiceEndpoints(environment);
