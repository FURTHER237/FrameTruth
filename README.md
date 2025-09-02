## Forensic-Tool UI — Install and Run (Windows)

This guide shows how to install and run the frontend UI found in `Forensic-Tool-UI/` using Node.js and npm on Windows.

### Prerequisites
- **Node.js + npm**: Install from `https://nodejs.org/` (LTS recommended). After install, verify:

```powershell
node -v
npm -v
```

### Get to the project folder
Open PowerShell and change directory to the UI folder. If your path has spaces, quote it.

```powershell
cd "cd ..\GitHub\FrameTruth\Forensic-Tool-UI"
```

If `cd` fails, ensure the folder exists and that you are not trying to `cd` into a file like `vite.config.js`.

### Install dependencies

```powershell
npm install
```

### Start the dev server

```powershell
npm run dev
```

You should see a URL like `http://localhost:5173/`. Open it in your browser.

Notes:
- To access from other devices on your network, run with host exposure:

```powershell
npm run dev -- --host
```

### Build for production

```powershell
npm run build
```

Then preview the production build locally:

```powershell
npm run preview
```

### Troubleshooting
- **Cannot change directory**: Use quotes around the full path, and make sure you’re pointing to the folder, not a file.
  - Correct: `cd ..\GitHub\FrameTruth\Forensic-Tool-UI"`
  
- **Port already in use (5173)**: Close the other app or specify a different port:

```powershell
npm run dev -- --port 5174
```

- **PostCSS/Vite ESM warning**: You may see a warning about module type. It’s safe to ignore for development. If desired, you can add `"type": "module"` in `Forensic-Tool-UI/package.json` to silence the warning.
- **Vulnerabilities after install**: Optional fix (may apply breaking changes):

```powershell
npm audit fix --force
```

### Project layout (relevant folder)
- `Forensic-Tool-UI/`: Vite + React frontend
  - `src/`: Application source code
  - `index.html`: App entry HTML
  - `package.json`: Scripts and dependencies

That’s it — you can now run the UI locally.

# FrameTruth