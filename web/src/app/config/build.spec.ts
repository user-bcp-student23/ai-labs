import { mkdtempSync, mkdirSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { readConfiguration, readOrigin, runBuild } from '../../../scripts/build.mjs';

const temporaryWorkspaces: string[] = [];

afterEach(() => {
  for (const workspace of temporaryWorkspaces.splice(0)) {
    rmSync(workspace, { recursive: true, force: true });
  }
});

function createWorkspace() {
  const workspace = mkdtempSync(join(tmpdir(), 'web-build-test-'));
  mkdirSync(join(workspace, 'src', 'environments'), { recursive: true });
  temporaryWorkspaces.push(workspace);
  return workspace;
}

describe('build configuration', () => {
  it('defaults to production and accepts the configured Angular environments', () => {
    expect(readConfiguration([])).toBe('production');
    expect(readConfiguration(['--configuration=development'])).toBe('development');
    expect(readConfiguration(['-c', 'production'])).toBe('production');
  });

  it('requires an absolute HTTP(S) origin and normalizes its trailing slash', () => {
    expect(readOrigin('AUTH_SERVICE_ORIGIN', {
      AUTH_SERVICE_ORIGIN: 'https://auth.example.invalid/'
    })).toBe('https://auth.example.invalid');
    expect(() => readOrigin('AUTH_SERVICE_ORIGIN', {})).toThrow(
      'AUTH_SERVICE_ORIGIN is required for a production build.'
    );
    expect(() => readOrigin('AUTH_SERVICE_ORIGIN', {
      AUTH_SERVICE_ORIGIN: 'https://auth.example.invalid/path'
    })).toThrow('must be an absolute HTTP(S) origin without a path.');
  });

  it('generates production origins for Angular and removes the generated file afterward', () => {
    const workspaceRoot = createWorkspace();
    const generatedFile = join(
      workspaceRoot,
      'src',
      'environments',
      'environment.production.generated.ts'
    );
    const executeBuild = vi.fn(() => {
      const generatedEnvironment = readFileSync(generatedFile, 'utf8');
      expect(generatedEnvironment).toContain('https://auth.example.invalid');
      expect(generatedEnvironment).toContain('https://api.example.invalid');
      return { status: 0 };
    });

    expect(runBuild(['--configuration=production'], {
      workspaceRoot,
      environment: {
        AUTH_SERVICE_ORIGIN: 'https://auth.example.invalid',
        API_SERVICE_ORIGIN: 'https://api.example.invalid'
      },
      executeBuild
    })).toBe(0);
    expect(executeBuild).toHaveBeenCalledOnce();
    expect(() => readFileSync(generatedFile, 'utf8')).toThrow();
  });

  it('runs development builds without production origins and returns the CLI status', () => {
    const executeBuild = vi.fn(() => ({ status: 2 }));

    expect(runBuild(['--configuration=development'], {
      workspaceRoot: createWorkspace(),
      environment: {},
      executeBuild
    })).toBe(2);
    expect(executeBuild).toHaveBeenCalledOnce();
  });

  it('rejects unsupported configurations and propagates process launch errors', () => {
    expect(() => runBuild(['--configuration=test'], {
      workspaceRoot: createWorkspace(),
      environment: {},
      executeBuild: vi.fn()
    })).toThrow('Unsupported Angular build configuration: test');

    expect(() => runBuild(['--configuration=development'], {
      workspaceRoot: createWorkspace(),
      environment: {},
      executeBuild: vi.fn(() => ({ error: new Error('spawn failed'), status: null }))
    })).toThrow('spawn failed');
  });
});
