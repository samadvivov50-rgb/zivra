const { spawnSync } = require("child_process");
const { getSmokeRuntime } = require("./runtime");

module.exports = async () => {
  const runtime = getSmokeRuntime();
  spawnSync(
    "powershell.exe",
    ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", runtime.stopScript, "-Quiet", "-StateName", runtime.stateName],
    {
      cwd: runtime.repoRoot,
      encoding: "utf8",
    },
  );
};
