const { execFileSync } = require("node:child_process");
const path = require("node:path");

// Delegate timing to the project's Python fixture so both entry points agree.
const root = path.resolve(__dirname, "../..");
const result = execFileSync("python", [
  "-c",
  "from fixture.units import frames_to_ms; print(frames_to_ms(30, 60))",
], { cwd: root, encoding: "utf8" });

console.log(result.trim() + " ms");
