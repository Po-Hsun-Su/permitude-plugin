"""Permitude's pre-tool hook. It puts into the tool call what the model
cannot type: the bytes of the design file the call names, the version of the
Permitude reference copy sitting beside it, and the property this folder is
bound to.

Which folder that is comes from the agent. Claude Code names it in
``CLAUDE_PROJECT_DIR``; Codex CLI runs this hook inside it; Antigravity CLI
sends it as ``workspacePaths`` and runs this hook from the installed plugin's
own directory instead, so nothing here may be read relative to the working
directory. An Antigravity run started without ``--add-dir`` sends no workspace
at all: a design named by a relative path is then not found, and the server
refuses the build by naming the path it tried — never a design that arrives
empty.
"""
import json,os,sys

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
    without Codex's own approval prompt. Told apart from Claude Code by the
    ``turn_id`` field only Codex sends and the ``PLUGIN_ROOT`` variable only
    Codex sets; Claude Code never receives the allow, so its permission
    prompt is untouched.
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

d=json.load(sys.stdin)
shape=envelope(d)
if shape=='dispatch':
    call=dict((d.get('toolCall') or {}).get('args') or {})
    if str(call.get('ServerName') or '')!='permitude':
        print('{}')
        sys.exit()
    i=dict(call.get('Arguments') or {})
    n=str(call.get('ToolName') or '')
    root=(d.get('workspacePaths') or ['.'])[0]
else:
    i=dict(d.get('tool_input') or {})
    n=str(d.get('tool_name') or '')
    root=os.environ.get('CLAUDE_PROJECT_DIR') or '.'
if n.endswith('deck_build'):
    p=i.pop('path','')
    if p and not os.path.isabs(p) and not os.path.exists(p):
        p=os.path.join(root,p)
    i['path_read']=p
    try: i['source']=open(p,encoding='utf-8').read()
    except Exception: i['source']=''
    try: i['sdk_version']=open(os.path.join(os.path.dirname(os.path.abspath(p)),'cadkit','VERSION'),encoding='utf-8').read().strip()
    except Exception: pass
try: i['site_data']=open(os.path.join(root,'.permitude','site_data.json'),encoding='utf-8').read()
except Exception: pass
if shape=='dispatch':
    print(json.dumps({'decision':'allow','overwrite':{'Arguments':i}}))
else:
    out={'hookEventName':'PreToolUse','updatedInput':i}
    if shape=='replace-allow':
        out['permissionDecision']='allow'
    print(json.dumps({'hookSpecificOutput':out}))
