import { spawn } from 'child_process';
import { createServer, build } from 'vite';
import electronPath from 'electron';
import path from 'path';

const isDev = process.env.NODE_ENV === 'development';

async function startRenderer() {
  const server = await createServer({
    configFile: './vite.config.ts',
    mode: 'development',
  });
  await server.listen();
  server.printUrls();
  return server;
}

async function startElectron() {
  const electron = spawn(String(electronPath), ['.'], {
    stdio: 'inherit',
    env: {
      ...process.env,
      NODE_ENV: 'development',
      VITE_DEV_SERVER_URL: 'http://localhost:5173',
    },
  });
  
  electron.on('close', () => {
    process.exit();
  });
}

async function main() {
  try {
    await build({
      configFile: './vite.config.ts',
      mode: 'development',
      build: {
        outDir: 'dist-electron',
      },
    });
    
    await startElectron();
  } catch (e) {
    console.error(e);
    process.exit(1);
  }
}

main();
