const fs = require("fs");
const { spawnSync } = require("child_process");
const { getSmokeRuntime } = require("./runtime");

function runPowerShell(scriptPath, args) {
  const command = spawnSync(
    "powershell.exe",
    ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", scriptPath, ...args],
    {
      cwd: getSmokeRuntime().repoRoot,
      encoding: "utf8",
    },
  );

  if (command.status !== 0) {
    const details = [command.stdout, command.stderr].filter(Boolean).join("\n").trim();
    throw new Error(`PowerShell command failed: ${scriptPath}\n${details}`);
  }
}

module.exports = async () => {
  const runtime = getSmokeRuntime();

  fs.rmSync(runtime.dataDir, { recursive: true, force: true });
  runPowerShell(runtime.stopScript, ["-Quiet", "-StateName", runtime.stateName]);
  runPowerShell(runtime.startScript, [
    "-NoOpenBrowser",
    "-ForceRestart",
    "-BindHost",
    "0.0.0.0",
    "-Port",
    String(runtime.port),
    "-StateName",
    runtime.stateName,
    "-DataDir",
    runtime.dataDir,
    "-HealthTimeoutSeconds",
    "60",
  ]);
};
