/**
 * Write-time gate for AGENTS.md / CLAUDE.md / GEMINI.md / copilot-instructions.md.
 * Blocks new uncommented durable instructions. Existing uncommented files stay editable.
 */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const EXT_DIR = dirname(fileURLToPath(import.meta.url));
const GATE = join(EXT_DIR, "..", "skills", "prompt-comments", "scripts", "gate.py");

function runGate(payload: unknown): { code: number; stdout: string; stderr: string } {
  if (!existsSync(GATE)) {
    return { code: 0, stdout: "", stderr: "" };
  }
  const result = spawnSync("python3", [GATE], {
    input: JSON.stringify(payload),
    encoding: "utf8",
    timeout: 4000,
  });
  if (result.error) {
    return { code: 0, stdout: "", stderr: "" };
  }
  return {
    code: result.status ?? 0,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
  };
}

function denyReason(stdout: string, stderr: string): string {
  try {
    const data = JSON.parse(stdout) as { reason?: string };
    if (data.reason) return data.reason;
  } catch {
    // fall through
  }
  return stderr.trim() || "prompt-comments: uncommented durable instruction";
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event) => {
    const name = event.toolName;
    let payload: Record<string, unknown> | null = null;

    if (name === "edit") {
      payload = {
        tool: "edit",
        input: {
          path: (event.input as { path?: string }).path,
          old_string: (event.input as { old_str?: string }).old_str,
          new_string: (event.input as { new_str?: string }).new_str,
        },
      };
    } else if (name === "ipython") {
      payload = {
        tool: "ipython",
        input: { code: (event.input as { code?: string }).code },
      };
    } else if (name === "bash") {
      payload = {
        tool: "bash",
        input: { command: (event.input as { command?: string }).command },
      };
    }

    if (!payload) return undefined;

    const result = runGate(payload);
    if (result.code === 2) {
      return { block: true, reason: denyReason(result.stdout, result.stderr) };
    }
    return undefined;
  });
}
