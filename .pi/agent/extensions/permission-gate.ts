/**
 * Permission Gate Extension
 *
 * Blocks any tool call that could modify state (write, edit, bash, etc.)
 * and asks the user for confirmation before allowing it to proceed.
 *
 * Read-only tools are always allowed without prompting:
 *   - read       (read file contents)
 *   - bash       (only safe read-only commands: ls, cat, grep, find, echo, pwd, etc.)
 *
 * Everything else requires explicit user approval.
 */

import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

// Tools that are always allowed unconditionally (no bash logic needed)
const ALWAYS_ALLOWED_TOOLS = new Set(["read"]);

// For bash, commands that begin with these prefixes are considered read-only.
// The check is applied after stripping leading whitespace and common env-var prefixes.
// Deliberately conservative: when in doubt, omit and let the user confirm.
const READ_ONLY_BASH_COMMANDS = new Set([
  "ls",
  "ll",
  "la",
  "cat",
  "bat",
  "head",
  "tail",
  "less",
  "more",
  "grep",
  "rg",
  "ag",
  "ack",
  "find",
  "fd",
  "locate",
  "which",
  "whereis",
  "type",
  "echo",
  "printf",
  "pwd",
  "whoami",
  "id",
  "hostname",
  "uname",
  "date",
  "env",
  "printenv",
  "wc",
  "sort",
  "uniq",
  "cut",
  "sed",   // sed without -i is read-only (prints to stdout); -i check applied below
  "tr",
  "diff",
  "comm",
  "stat",
  "file",
  "du",
  "df",
  "lsof",
  "ps",
  "top",
  "htop",
  "uptime",
  "free",
  "vmstat",
  "iostat",
  "netstat",
  "ss",
  "nslookup",
  "dig",
  "host",
  "git",    // only safe git subcommands checked below
  "man",
  "help",
  "info",
  "tldr",
  "tree",
  "jq",
  "yq",
  "xmllint",
]);

// git subcommands that are read-only
const READ_ONLY_GIT_SUBCOMMANDS = new Set([
  "status",
  "log",
  "diff",
  "show",
  "branch",
  "tag",
  "remote",
  "fetch",  // fetch is arguably write (updates refs) — but included as low-risk
  "ls-files",
  "ls-remote",
  "rev-parse",
  "rev-list",
  "describe",
  "shortlog",
  "blame",
  "grep",
  "stash",  // stash list / stash show are read-only; stash push is write — handled below
]);

/**
 * Parse the first "real" command from a potentially compound shell string.
 * Handles simple cases like `VAR=value cmd args` and pipelines.
 */
function extractLeadingCommand(raw: string): { cmd: string; rest: string } {
  // Strip leading env-var assignments like FOO=bar BAZ=qux
  let s = raw.trim();
  s = s.replace(/^(\w+=\S*\s+)+/, "");

  // Take the first word (the command name, possibly a path like /usr/bin/ls)
  const match = s.match(/^([^\s|;&]+)(.*)/s);
  if (!match) return { cmd: "", rest: "" };

  const cmd = match[1].split("/").pop() ?? match[1]; // basename
  const rest = match[2] ?? "";
  return { cmd, rest };
}

/**
 * Returns true if a bash command string is considered read-only.
 */
function isBashReadOnly(command: string): boolean {
  // Multi-statement / piped commands — check each segment
  // Split on ; && || newlines AND single pipes (| but not ||, already handled)
  const parts = command.split(/;|\n|&&|\|\||\|/);
  if (parts.length > 1) {
    // Only safe if ALL parts are read-only
    return parts.every((part) => isBashReadOnly(part.trim()));
  }

  const { cmd, rest } = extractLeadingCommand(command);
  if (!cmd) return true; // empty — harmless

  if (!READ_ONLY_BASH_COMMANDS.has(cmd)) return false;

  // Extra checks for commands that have dangerous subcommands/flags

  // sed -i modifies files in place
  if (cmd === "sed" && /\s-[a-zA-Z]*i/.test(rest)) return false;

  // git — check subcommand
  if (cmd === "git") {
    const sub = rest.trim().split(/\s+/)[0];
    if (!sub) return true; // bare `git` — harmless
    if (!READ_ONLY_GIT_SUBCOMMANDS.has(sub)) return false;
    // git stash push / pop / drop / apply are write operations
    if (sub === "stash") {
      const stashSub = rest.trim().split(/\s+/)[1];
      if (stashSub && !["list", "show"].includes(stashSub)) return false;
    }
    return true;
  }

  return true;
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event, ctx) => {
    const { toolName } = event;

    // Always allow read-only tools
    if (ALWAYS_ALLOWED_TOOLS.has(toolName)) return undefined;

    // For bash, check whether the command is read-only
    if (toolName === "bash") {
      const command = (event.input as { command: string }).command;
      if (isBashReadOnly(command)) return undefined;
    }

    // Everything else needs user confirmation
    if (!ctx.hasUI) {
      return {
        block: true,
        reason: `Tool "${toolName}" requires user confirmation but no UI is available.`,
      };
    }

    // Build a readable summary of what's about to happen
    let description = `Tool: ${toolName}`;
    if (toolName === "bash") {
      const command = (event.input as { command: string }).command;
      description = `bash command:\n\n  ${command}`;
    } else if (toolName === "write") {
      const input = event.input as { path: string };
      description = `write file:\n\n  ${input.path}`;
    } else if (toolName === "edit") {
      const input = event.input as { path: string };
      description = `edit file:\n\n  ${input.path}`;
    } else {
      // Generic: show full input as JSON
      description = `${toolName}:\n\n  ${JSON.stringify(event.input, null, 2).replace(/\n/g, "\n  ")}`;
    }

    const choice = await ctx.ui.select(
      `⚠️  Permission required\n\n  ${description}\n\nAllow?`,
      ["Yes", "No"],
    );

    if (choice !== "Yes") {
      return { block: true, reason: "Blocked by user" };
    }

    return undefined;
  });
}
