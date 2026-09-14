# The MCP bridge — driving a live TouchDesigner session

Everything here was verified working against this machine on **2026-08-09**
(TD 099.2025.33070, API server 1.5.0, MCP server 2.0.0). It is not summarized
from the project README.

Package: [`8beeeaaat/touchdesigner-mcp`](https://github.com/8beeeaaat/touchdesigner-mcp)

## Architecture

Two halves that must both be present:

```
Claude ──stdio──> touchdesigner-mcp-server (npx)
                        │ HTTP 127.0.0.1:9981
                        ▼
                 WebServer DAT inside /project1/mcp_webserver_base
```

The TD half is a `.tox` containing four nodes:

| Node                   | Type         | Role                            |
| ---------------------- | ------------ | ------------------------------- |
| `mpc_webserver`        | webserverDAT | the actual HTTP listener        |
| `import_modules`       | textDAT      | puts `modules/` on `sys.path`   |
| `mcp_webserver_script` | textDAT      | request handling                |
| `parameter1`           | parameterDAT | exposes Port / Active / Restart |

## Installation

The `.tox` is **not** in the npm package. It ships as a separate release asset:

```bash
curl -sL -o td-mcp.zip \
  https://github.com/8beeeaaat/touchdesigner-mcp/releases/download/vX.Y.Z/touchdesigner-mcp-td.zip
unzip td-mcp.zip -d touchdesigner-mcp-td/
```

Then in TouchDesigner: drag `mcp_webserver_base.tox` onto the `/project1`
network, and save.

### Four things that break it

1. **Version skew.** The release tag and the npm `touchdesigner-mcp-server`
   version must match (both `2.0.0` here). Check with
   `npm ls -g touchdesigner-mcp-server` or the `package.json` in the npx cache.
2. **Port.** The client has `9981` **hardcoded** — verified by grepping `dist/`,
   8 occurrences, and there is no env var to override it. The `.tox`'s `Port`
   custom parameter must read 9981. Check it visually after import; the shipped
   default may differ.
3. **`Active` must be on.** The WebServer DAT's `active` par is an expression
   bound to `op('parameter1')['Active',1]`.
4. **Folder layout.** `import_modules.py` does
   `os.path.dirname(parent().par.externaltox.eval())` then looks for `modules/`
   next to it. `import_modules.py`, `mcp_webserver_base.tox`, and `modules/`
   must stay siblings. Moving the whole folder is fine; moving one item is not.

`PyYAML` is required by `import_modules.py` and **is bundled** in TD 2025's
Python 3.11 site-packages — no pip step needed.

## Tools

| Tool                                                             | Use                                                |
| ---------------------------------------------------------------- | -------------------------------------------------- |
| `get_td_info`                                                    | version handshake; the fastest connection test     |
| `get_td_nodes`                                                   | list nodes under a path, grouped by type           |
| `get_td_node_parameters`                                         | real parameter names and values on a real node     |
| `get_td_node_errors`                                             | node + descendant errors                           |
| `create_td_node` / `delete_td_node`                              | single node create/destroy                         |
| `update_td_node_parameters`                                      | set parameters by dict                             |
| `exec_node_method`                                               | call a method on a node                            |
| `execute_python_script`                                          | arbitrary Python — the one that does the real work |
| `get_top_image`                                                  | **capture a TOP's output as a viewable image**     |
| `get_td_classes` / `get_td_class_details` / `get_td_module_help` | API docs lookup                                    |

## Working practice

**Build with `execute_python_script`, not `create_td_node`.** One script creates
the nodes, positions them (`node.nodeX/nodeY`), wires them
(`dst.inputConnectors[i].connect(src)`), and sets parameters atomically. Six
separate tool calls become one, and you control layout so the network is legible
to the human looking at it.

**Never guess a parameter name — read it.**

```python
[p.name for p in op('/project1/thing').pars()]
```

Guessing fails constantly and silently-ish. Verified misses on real nodes:
`levelTOP.gain` does not exist (it is **`opacity`**); `noiseTOP.monochrome` does
not exist (it is **`mono`**). Wrap sets in try/except and return a per-parameter
status dict so one bad name doesn't abort the whole build:

```python
log = {}
def setp(node, name, val):
    try:
        setattr(node.par, name, val); log[f'{node.name}.{name}'] = 'ok'
    except Exception as e:
        log[f'{node.name}.{name}'] = 'FAIL ' + str(e)[:60]
```

**`me` is `None` in the exec context.** The script runs in a bare namespace, not
inside an operator. `me.time.rate` raises
`AttributeError: 'NoneType' object has no attribute 'time'`. Use absolute paths
(`op('/project1/x')`), and `project.cookRate` / `absTime` instead of `me.time`.

**Return a value on the last line** to get it back as structured output; `print()`
also surfaces. Long results truncate — pass `detailLevel='detailed'` or return a
smaller dict.

**Close the loop with `get_top_image`.** Change → capture → look → adjust,
without the human narrating what's on screen. This is the capability that makes
the bridge worth installing.

**Check errors after structural changes:** `op('/project1').errors(recurse=True)`.

**Do not create or destroy nodes from inside a cook.** The usual TD rule still
applies here; schedule with `run(..., delayFrames=1)` if a script runs in a cook
context.

## The live session and the file are different things

The bridge shows RAM. `toeexpand` shows disk. They diverge the moment anything
changes after the last save, and the human's "I saved it" may predate your last
edit — verified in practice, with a 51-second gap that silently dropped a fix.

Before trusting that work persisted, compare:

```bash
stat -f "%Sm %N" -t "%H:%M:%S" *.toe     # save time vs. when you made the change
```

and confirm structurally in the expanded file (see `project-workflow.md`).
Checking both paths catches what neither catches alone.

## When a network misbehaves, check resolution first

A large share of "this looks wrong and reports no error" turns out to be
resolution inheritance rather than anything to do with the bridge. See
**Resolution propagates** in `operators.md` — the `feedbackTOP` unwired-input trap
especially, which silently collapsed a whole 1280 chain to 128.

The bridge makes this fast to diagnose: walk the chain with

```python
{n: [op('/project1/'+n).width, op('/project1/'+n).height] for n in chain}
```

and compare against what the resolution parameters claim. They disagree routinely,
and the actual size is the one that matters.
