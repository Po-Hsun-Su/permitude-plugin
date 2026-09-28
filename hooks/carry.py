"""Permitude's pre-tool hook. It puts into a Permitude tool call what the
model cannot type: the bytes of the design file the call names, the version
of the Permitude reference copy sitting beside it, and the property this
folder is bound to.

What it refuses, so that nothing else ever leaves this machine through it:

- **Any other server's call.** A tool of the same name on another MCP server
  is left exactly as it was: nothing added, nothing approved.
- **Any file outside the folder the agent is working in.** Every path is
  resolved with its links followed, and only a regular file that is still
  inside that folder is read. An absolute path elsewhere, a ``..`` that climbs
  out, a link that points out, or a folder is not read.
- **A design that is not a ``.py`` file, or is larger than the server
  accepts.** It is not read either.

Beside the design goes where it sits: its path inside that folder, however
the call spelled it, or only the file's name when it lies anywhere else. No
folder outside the working folder is ever named to the server.

A design that is not read travels as an empty ``source`` beside that name,
and the server's answer names it and these rules, so the agent can tell the
customer what to move.

Which folder that is comes from the agent. Claude Code names it in
``CLAUDE_PROJECT_DIR``; Codex CLI runs this hook inside it; Antigravity CLI
sends it as ``workspacePaths`` and runs this hook from the installed plugin's
own directory instead, so nothing here may be read relative to the working
directory. An Antigravity run started without ``--add-dir`` sends no workspace
at all: nothing is read, and the server refuses the build by naming the path
it was given — never a design that arrives empty.
"""
import json,os,re,sys

SERVER='permitude'
TOOLS=('read_reference','read_project','read_gallery','set_project','deck_build','report_issue')
MAX_BYTES=500_000

def envelope(d):
    """Which hook protocol this payload arrived on, as the one thing that
    differs between the agents Permitude supports: how a pre-tool hook hands
    back the arguments it rewrote.

    ``replace`` — Claude Code. Events ``PreToolUse`` and ``PostToolUse``; the
    call's arguments are ``tool_input`` and the answer is
    ``hookSpecificOutput.updatedInput``, the whole replacement argument
    object, so an argument this hook popped is gone from the call.
    https://docs.claude.com/en/docs/claude-code/hooks

    ``replace-allow`` — Codex CLI. The same events and answer as ``replace``,
    but Codex reports ``updatedInput`` as an error unless the same answer
    carries ``permissionDecision: "allow"``, which also lets the call proceed
    without Codex's own approval prompt. That answer is only ever given to a
    call :func:`permitude_call` has found to be Permitude's own. Told apart
    from Claude Code by the ``turn_id`` field only Codex sends and the
    ``PLUGIN_ROOT`` variable only Codex sets; Claude Code never receives the
    allow, so its permission prompt is untouched.
    https://learn.chatgpt.com/docs/hooks

    ``dispatch`` — Antigravity CLI. Every MCP call is one dispatcher tool
    named ``call_mcp_tool``, so the call arrives nested: the server, the tool
    and the tool's own arguments are ``toolCall.args.ServerName``,
    ``ToolName`` and ``Arguments``. The answer is
    ``{"decision": "allow", "overwrite": {"Arguments": …}}`` — ``overwrite``
    is a shallow top-level merge of ``toolCall.args``, so replacing the whole
    ``Arguments`` object is what lets a popped argument disappear, and the
    ``allow`` is what lets the call proceed. Told apart by the ``toolCall``
    field, which no other agent sends. ``overwrite`` is documented only
    inside the ``agy`` binary's own embedded documentation, not on the public
    hooks page; the rest is measured against Antigravity CLI 1.1.28.
    https://antigravity.google/docs/cli
    """
    if 'toolCall' in d:
        return 'dispatch'
    if 'turn_id' in d or os.environ.get('PLUGIN_ROOT'):
        return 'replace-allow'
    return 'replace'

def permitude_call(d):
    """The Permitude tool this payload calls and that call's arguments, or
    ``None`` when the call goes to any other server.

    Claude Code and Codex name the server inside the tool's own name —
    ``mcp__plugin_permitude_permitude__<tool>`` for the installed plugin,
    ``mcp__permitude__<tool>`` for a server registered under that name by
    hand or by Codex. Antigravity names it as the call's ``ServerName``.
    """
    if envelope(d)=='dispatch':
        call=(d.get('toolCall') or {}).get('args') or {}
        server,tool,args=call.get('ServerName'),call.get('ToolName'),call.get('Arguments')
    else:
        m=re.fullmatch(r'mcp__(?:plugin_permitude_)?(permitude)__([a-z_]+)',str(d.get('tool_name') or ''))
        server,tool,args=(m.group(1),m.group(2),d.get('tool_input')) if m else (None,None,None)
    if server!=SERVER or tool not in TOOLS:
        return None
    return tool,dict(args) if isinstance(args,dict) else {}

def workspace(d):
    """The folder the agent is working in, or ``None`` when it named none."""
    if envelope(d)=='dispatch':
        return (d.get('workspacePaths') or [None])[0]
    return os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()

def named_inside(root,path):
    """``path`` as the server is told it: relative to ``root`` when, with
    every link followed, it leads inside ``root``; the file's name alone
    otherwise, or when there is no ``root``."""
    try:
        top=os.path.realpath(root)
        real=os.path.realpath(os.path.join(root,path))
        if os.path.commonpath([top,real])==top:
            return os.path.relpath(real,top)
    except Exception:
        pass
    return os.path.basename(os.path.normpath(path)) or path

def read_inside(root,path,suffix=''):
    """The text of ``path`` (relative to ``root``, or absolute) when, with
    every link followed, it is a regular file inside ``root`` whose name ends
    in ``suffix`` and whose size is at most ``MAX_BYTES``; ``None`` for
    anything else."""
    if not root or not path:
        return None
    try:
        top=os.path.realpath(root)
        real=os.path.realpath(os.path.join(root,path))
        if os.path.commonpath([top,real])!=top or not real.endswith(suffix):
            return None
        if not os.path.isfile(real) or os.path.getsize(real)>MAX_BYTES:
            return None
        with open(real,encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

d=json.load(sys.stdin)
call=permitude_call(d)
if call is None:
    print('{}')
    sys.exit()
tool,i=call
root=workspace(d)
if tool=='deck_build':
    p=str(i.pop('path','') or '')
    i['path_read']=named_inside(root,p) if p else p
    i['source']=read_inside(root,p,'.py') or ''
    if i['source']:
        beside=os.path.dirname(os.path.realpath(os.path.join(root,p)))
        version=read_inside(root,os.path.join(beside,'cadkit','VERSION'))
        if version:
            i['sdk_version']=version.strip()
binding=read_inside(root,os.path.join('.permitude','site_data.json'))
if binding is not None:
    i['site_data']=binding
if envelope(d)=='dispatch':
    print(json.dumps({'decision':'allow','overwrite':{'Arguments':i}}))
else:
    out={'hookEventName':'PreToolUse','updatedInput':i}
    if envelope(d)=='replace-allow':
        out['permissionDecision']='allow'
    print(json.dumps({'hookSpecificOutput':out}))
