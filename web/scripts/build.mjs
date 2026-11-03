import { spawnSync } from 'node:child_process';
import { rmSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const defaultWorkspaceRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const productionEnvironmentRelativePath = 'src/environments/environment.production.generated.ts';

export function readConfiguration(argumentsList) {
  for (let index = 0; index < argumentsList.length; index += 1) {
    const argument = argumentsList[index];
    if (argument.startsWith('--configuration=')) {
      return argument.split('=', 2)[1];
    }
    if (argument === '--configuration' || argument === '-c') {
      return argumentsList[index + 1] ?? '';
    }
  }
  return 'production';
}

export function readOrigin(environmentVariable, environment = process.env) {
  const value = environment[environmentVariable]?.trim();
  if (!value) {
    throw new Error(`${environmentVariable} is required for a production build.`);
  }

  let origin;
  try {
    origin = new URL(value);
  } catch {
    throw new Error(`${environmentVariable} must be an absolute HTTP(S) origin without a path.`);
  }

  if (
    !['http:', 'https:'].includes(origin.protocol) ||
    origin.username ||
    origin.password ||
    origin.pathname !== '/' ||
    origin.search ||
    origin.hash
  ) {
    throw new Error(`${environmentVariable} must be an absolute HTTP(S) origin without a path.`);
  }

  return origin.origin;
}

export function runBuild(buildArguments = process.argv.slice(2), options = {}) {
  const {
    environment = process.env,
    workspaceRoot = defaultWorkspaceRoot,
    executeBuild = executeAngularBuild
  } = options;
  const configuration = readConfiguration(buildArguments);

  if (configuration !== 'development' && configuration !== 'production') {
    throw new Error(`Unsupported Angular build configuration: ${configuration}`);
  }

  const generatedEnvironmentPath = resolve(workspaceRoot, productionEnvironmentRelativePath);
  if (configuration === 'production') {
    const productionOrigins = {
      authServiceOrigin: readOrigin('AUTH_SERVICE_ORIGIN', environment),
      apiServiceOrigin: readOrigin('API_SERVICE_ORIGIN', environment)
    };
    writeFileSync(
      generatedEnvironmentPath,
      `export const environment = ${JSON.stringify(productionOrigins, null, 2)} as const;\n`,
      'utf8'
    );
  }

  try {
    const build = executeBuild(workspaceRoot, buildArguments);
    if (build.error) {
      throw build.error;
    }
    return build.status ?? 1;
  } finally {
    if (configuration === 'production') {
      rmSync(generatedEnvironmentPath, { force: true });
    }
  }
}

function executeAngularBuild(workspaceRoot, buildArguments) {
  const angularCliPath = resolve(workspaceRoot, 'node_modules', '@angular', 'cli', 'bin', 'ng.js');
  return spawnSync(
    process.execPath,
    [angularCliPath, 'build', ...buildArguments],
    { cwd: workspaceRoot, stdio: 'inherit' }
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = runBuild();
}
