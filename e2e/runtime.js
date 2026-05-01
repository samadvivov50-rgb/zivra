const path = require("path");
const fs = require("fs");

function detectSystemChromiumExecutable() {
  const override = process.env.ZIVRA_PLAYWRIGHT_EXECUTABLE || "";
  const candidates = [
    override,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ].filter(Boolean);

  return candidates.find((candidate) => fs.existsSync(candidate)) || "";
}

function getSmokeRuntime() {
  const repoRoot = path.resolve(__dirname, "..");
  const port = Number(process.env.ZIVRA_PLAYWRIGHT_PORT || "8011");
  const stateName = process.env.ZIVRA_PLAYWRIGHT_STATE || "playwright-smoke";
  const dataDir = path.resolve(
    process.env.ZIVRA_PLAYWRIGHT_DATA_DIR || path.join(repoRoot, "backend", "data", "test-runs", stateName),
  );

  return {
    repoRoot,
    port,
    stateName,
    dataDir,
    executablePath: detectSystemChromiumExecutable(),
    baseUrl: process.env.ZIVRA_PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${port}`,
    startScript: path.join(repoRoot, "scripts", "start-zivra.ps1"),
    stopScript: path.join(repoRoot, "scripts", "stop-zivra.ps1"),
  };
}

module.exports = {
  getSmokeRuntime,
};
