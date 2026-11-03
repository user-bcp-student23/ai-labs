import { afterEach, describe, expect, it, vi } from 'vitest';
import '@angular/compiler';
import type { ChangeDetectorRef, NgZone } from '@angular/core';
import type { Router } from '@angular/router';
import axios from 'axios';
import { DashboardComponent } from './dashboard.component';

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}));

function createStorage(values: Record<string, string>) {
  const storedValues = new Map(Object.entries(values));
  return {
    clear: vi.fn(() => storedValues.clear()),
    getItem: vi.fn((key: string) => storedValues.get(key) ?? null),
    key: vi.fn((index: number) => [...storedValues.keys()][index] ?? null),
    removeItem: vi.fn((key: string) => storedValues.delete(key)),
    setItem: vi.fn((key: string, value: string) => storedValues.set(key, value)),
    get length() {
      return storedValues.size;
    }
  } satisfies Storage;
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('DashboardComponent service endpoint', () => {
  it('loads tasks from the configured endpoint with the existing owner and auth header', async () => {
    vi.stubGlobal('localStorage', createStorage({
      workshop_token: 'test-token',
      workshop_user: JSON.stringify({ username: 'student' })
    }));
    vi.mocked(axios.get).mockResolvedValue({
      data: [{
        status: 'TODO',
        title: 'Review',
        description: 'Review tasks',
        priority: 'HIGH',
        owner: 'student'
      }]
    } as never);
    const router = {
      navigate: vi.fn().mockResolvedValue(true)
    } as unknown as Router;
    const changeDetector = {
      detectChanges: vi.fn()
    } as unknown as ChangeDetectorRef;
    const zone = {
      run: (callback: () => void) => callback()
    } as NgZone;
    const component = new DashboardComponent(router, changeDetector, zone);

    await component.ngOnInit();

    expect(axios.get).toHaveBeenCalledWith(
      'http://localhost:8000/api/tasks?owner=student',
      { headers: { Authorization: 'Bearer test-token' } }
    );
    expect(component.visibleTasks).toHaveLength(1);
  });

  it('handles a task request error without leaving the dashboard loading', async () => {
    vi.stubGlobal('localStorage', createStorage({
      workshop_token: 'test-token',
      workshop_user: JSON.stringify({ username: 'student' })
    }));
    vi.mocked(axios.get).mockRejectedValue({
      response: { data: { detail: 'Backend unavailable' } }
    });
    const changeDetector = {
      detectChanges: vi.fn()
    } as unknown as ChangeDetectorRef;
    const component = new DashboardComponent(
      { navigate: vi.fn() } as unknown as Router,
      changeDetector,
      { run: (callback: () => void) => callback() } as NgZone
    );

    await component.ngOnInit();

    expect(component.error).toBe('Backend unavailable');
    expect(component.loading).toBe(false);
    expect(changeDetector.detectChanges).toHaveBeenCalled();
  });

  it('clears session data and returns to login on logout', async () => {
    const storage = createStorage({
      workshop_token: 'test-token',
      workshop_user: JSON.stringify({ username: 'student' })
    });
    vi.stubGlobal('localStorage', storage);
    const router = {
      navigate: vi.fn().mockResolvedValue(true)
    } as unknown as Router;
    const component = new DashboardComponent(
      router,
      { detectChanges: vi.fn() } as unknown as ChangeDetectorRef,
      { run: (callback: () => void) => callback() } as NgZone
    );

    await component.logout();

    expect(storage.getItem('workshop_token')).toBeNull();
    expect(storage.getItem('workshop_user')).toBeNull();
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });
});
