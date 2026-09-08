"""The checks, offered to an agent, and every answer written down.

    glitch-mcp --repo .

WHAT THIS VERSION DOES NOT DO, stated first because the name of the eventual
product invites the opposite assumption. It gates nothing. It cannot pause,
refuse, block, or intercept any action the agent takes. It has no database
connection, no provider credential, and no network call. It runs the same six
checks the command line runs, over a repository it only reads, and it appends
what it was asked and what it answered to a local file.

That is deliberate and it is the whole first version. A server that stands
between an agent and a production database is a serious piece of software, and
the honest order is to earn the evidence first: run read-only for a while, read
the ledger, and find out what it WOULD have refused before giving it the power
to refuse anything. A gate built before that record exists is a guess with
permissions.

The one write. The checks themselves write nothing into the repository, which
is a promise the checker makes in its own docstring and has a test behind it.
This server breaks that promise in exactly one place, on purpose: it appends to
the ledger. Nothing else on disk is touched. `--no-ledger` turns even that off,
at the cost of the only thing here worth keeping.
"""
import argparse
import asyncio
import json
import pathlib
import sys

from . import __version__, cli
from .ledger import Ledger, LedgerError

try:
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError:  # pragma: no cover - exercised by the message, not the suite
    Server = None


MISSING_SDK = (
    "glitch-mcp needs the Model Context Protocol SDK, which the base package\n"
    "deliberately does not depend on:\n"
    "\n"
    "    pip install 'glitch-toolkit[mcp]'\n"
    "\n"
    "The checker itself has no dependencies and `glitch` still works without it."
)


def _text(payload):
    """One JSON blob as the tool's content.

    JSON rather than prose because the caller is a model that will act on it,
    and a sentence is something to interpret where a field is something to read.
    """
    return [
        types.TextContent(
            type="text", text=json.dumps(payload, indent=2, sort_keys=True, default=str)
        )
    ]


def describe_tools():
    """The tool list, built once and shared with the tests.

    Every one is annotated read-only, and every one of them is. If a tool that
    changes something is ever added here, that flag is the first thing to get
    wrong and the first thing a reviewer should check.
    """
    read_only = types.ToolAnnotations(read_only_hint=True, destructive_hint=False)
    return [
        types.Tool(
            name="glitch_status",
            title="Repository status",
            description=(
                "Which of the six bounded-autonomy practices are installed in this "
                "repository and which are not. Reads only. A step reported as failing "
                "usually means the reader has not yet written their own file for it "
                "(CLAUDE.md, FLEET.md, FLOOR.md, PLAN.md), which is work, not a bug."
            ),
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            annotations=read_only,
        ),
        types.Tool(
            name="glitch_check",
            title="Verify a practice",
            description=(
                "Run one step's check, or all of them. A step passes only when its "
                "artifact is present, runs, AND still refuses a deliberately broken "
                "case. Returns a receipt per passing step. Reads only."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "step": {
                        "type": "string",
                        "description": "one of: " + ", ".join(s.id for s in cli.STEPS),
                        "enum": [s.id for s in cli.STEPS],
                    }
                },
                "additionalProperties": False,
            },
            annotations=read_only,
        ),
        types.Tool(
            name="glitch_ledger_tail",
            title="Read the record",
            description=(
                "The most recent entries from this repository's append-only ledger: "
                "what was asked of this server and what it answered. Supersession is "
                "reported, never applied, so a superseded entry is still visible."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 25}
                },
                "additionalProperties": False,
            },
            annotations=read_only,
        ),
    ]


class GlitchTools:
    """The tool implementations, with the repository and ledger bound in.

    A class rather than module globals so the tests can stand one up against a
    temporary repository without a process, an environment variable, or a pipe.
    """

    def __init__(self, repo, ledger=None):
        self.repo = pathlib.Path(repo).resolve()
        self.ledger = ledger

    def _record(self, event, outcome, **fields):
        """Append to the ledger, and never fail a tool call because of it.

        A ledger that cannot be written is a real problem and the caller is told
        about it in the response, but an unwritable file is not a reason to
        refuse to answer a read-only question. The alternative is a server that
        stops working when a disk fills, which is a worse failure than a gap in
        a record that says it has a gap.
        """
        if self.ledger is None:
            return {"written": False, "reason": "ledger disabled with --no-ledger"}
        try:
            record = self.ledger.append(event, outcome, repo=str(self.repo), **fields)
            return {"written": True, "id": record["id"], "at": record["at"]}
        except (LedgerError, OSError) as e:
            return {"written": False, "reason": str(e)}

    def status(self):
        steps = []
        for step in cli.STEPS:
            result = step.check(self.repo)
            steps.append(
                {
                    "id": step.id,
                    "title": step.title,
                    "chapter": step.chapter,
                    "installed_and_refusing": result.ok,
                    # Not a count of failures. A step that passed has no first
                    # failure, and null says that rather than pretending to a
                    # reason it does not have.
                    "first_failure": result.failures[0] if result.failures else None,
                }
            )
        passing = sum(1 for s in steps if s["installed_and_refusing"])
        payload = {
            "repo": str(self.repo),
            "steps": steps,
            "passing": passing,
            "total": len(steps),
        }
        payload["ledger"] = self._record(
            "status", "ok", passing=passing, total=len(steps)
        )
        return payload

    def check(self, step_id=None):
        if step_id is None:
            steps = list(cli.STEPS)
        elif step_id in cli.BY_ID:
            steps = [cli.BY_ID[step_id]]
        else:
            # Refused, not guessed at. The command line behaves the same way and
            # there is a test for it; a server that helpfully picked the nearest
            # step would be answering a question nobody asked.
            payload = {
                "error": "no such step: {}".format(step_id),
                "steps": [s.id for s in cli.STEPS],
            }
            payload["ledger"] = self._record("check", "refused", requested=step_id)
            return payload

        results = []
        for step in steps:
            result = step.check(self.repo)
            results.append(
                {
                    "id": step.id,
                    "title": step.title,
                    "passed": result.ok,
                    "notes": list(result.notes),
                    "failures": list(result.failures),
                    # A receipt exists only for a step that passed. There is no
                    # such thing as a receipt for a failure, and an empty string
                    # here would read like one.
                    "receipt": cli.receipt_for(step.id, result.digest()) if result.ok else None,
                }
            )

        payload = {
            "repo": str(self.repo),
            "results": results,
            "all_passed": all(r["passed"] for r in results),
        }
        payload["ledger"] = self._record(
            "check",
            "pass" if payload["all_passed"] else "fail",
            steps=[r["id"] for r in results],
            receipts=[r["receipt"] for r in results if r["receipt"]],
        )
        return payload

    def ledger_tail(self, limit=25):
        if self.ledger is None:
            return {"error": "ledger disabled with --no-ledger", "records": []}
        records, unreadable = self.ledger.read(limit=limit)
        superseded = self.ledger.superseded_ids()
        for r in records:
            r["is_superseded"] = r.get("id") in superseded
        return {
            "path": str(self.ledger.path),
            "records": records,
            "returned": len(records),
            # Reported rather than repaired. A partial last line is what a
            # process killed mid-write leaves behind, and rewriting the file to
            # tidy it away is the one thing an append-only record must not do.
            "unreadable_lines": unreadable,
        }

    def dispatch(self, name, arguments):
        arguments = arguments or {}
        if name == "glitch_status":
            return self.status()
        if name == "glitch_check":
            return self.check(arguments.get("step"))
        if name == "glitch_ledger_tail":
            return self.ledger_tail(int(arguments.get("limit", 25)))
        raise KeyError(name)


def build_server(tools):
    """Wire the tool implementations to the protocol.

    Kept separate from `main` so a test can drive the handlers directly without
    a subprocess, and so the only thing `main` owns is argument parsing and the
    stdio transport.
    """

    async def on_list_tools(ctx, params):
        return types.ListToolsResult(tools=describe_tools())

    async def on_call_tool(ctx, params):
        try:
            payload = tools.dispatch(params.name, params.arguments)
        except KeyError:
            return types.CallToolResult(
                content=_text(
                    {
                        "error": "no such tool: {}".format(params.name),
                        "tools": [t.name for t in describe_tools()],
                    }
                ),
                is_error=True,
            )
        except Exception as e:  # noqa: BLE001 - a crash is an answer, not a hang
            tools._record("call", "error", tool=params.name, error=repr(e))
            return types.CallToolResult(
                content=_text({"error": "{}: {}".format(type(e).__name__, e)}),
                is_error=True,
            )
        return types.CallToolResult(content=_text(payload))

    return Server(
        "glitch",
        version=__version__,
        title="glitch",
        instructions=(
            "Read-only. Reports whether this repository's bounded-autonomy practices "
            "are installed and still refusing, and keeps an append-only record of "
            "every answer. It cannot block, pause or change anything."
        ),
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
    )


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--repo", default=".", help="the repository to read (default: here)")
    ap.add_argument("--ledger", default=None, help="where to append the record")
    ap.add_argument(
        "--no-ledger",
        action="store_true",
        help="answer questions but write nothing down (the record is the point; think first)",
    )
    args = ap.parse_args(argv)

    if Server is None:
        print(MISSING_SDK, file=sys.stderr)
        return 2

    repo = pathlib.Path(args.repo).resolve()
    if not repo.is_dir():
        print("no such repository: {}".format(repo), file=sys.stderr)
        return 2

    ledger = None if args.no_ledger else Ledger.for_repo(repo, args.ledger)
    tools = GlitchTools(repo, ledger)
    server = build_server(tools)

    async def serve():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(serve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
