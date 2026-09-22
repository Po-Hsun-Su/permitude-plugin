"""Permitude's post-tool hook. It spends what a Permitude result hands back:
one fetch line names a file from a closed set — the permit packet, the
Permitude reference copy it unpacks into ``cadkit/``, this property's starter
design, one build's scene — and one binding line records which property this
folder is bound to. The hook carries every byte and every credential, so
nothing the agent types has to.

Where it writes is the folder the agent is working in, read the way
``carry.py`` reads it.
"""
import json,sys,re,io,os,shutil,zipfile,base64,urllib.request,urllib.parse

def envelope(d):
    """Which hook protocol this payload arrived on, as the one thing that
    differs between the agents Permitude supports: where the tool's result is
    to be found, and what the hook may answer with.

    ``replace`` — Claude Code and Codex CLI. Events ``PreToolUse`` and
    ``PostToolUse``; the result arrives whole as ``tool_response`` and the
    answer is a sentence for the agent, ``additionalContext``, naming its own
    event beside it.
    https://docs.claude.com/en/docs/claude-code/hooks
    https://learn.chatgpt.com/docs/hooks

    ``dispatch`` — Antigravity CLI. Every MCP call is one dispatcher tool
    named ``call_mcp_tool``; the payload carries the call under ``toolCall``,
    the step's number as ``stepIdx``, ``error`` when the call failed, and no
    result at all when it succeeded. The result text is in the transcript
    file the payload names, one JSON object per line, and the object for this
    step is the one whose ``step_index`` is that number and whose ``type`` is
    ``GENERIC``: reading it by step is what keeps a hook from redeeming a
    line some earlier call left behind. The only answer this event takes is
    an empty object, so an Antigravity session is told what landed by the
    tool's own result rather than by this hook. Measured against Antigravity
    CLI 1.1.28.
    https://antigravity.google/docs/cli
    """
    return 'dispatch' if 'toolCall' in d else 'replace'

def result_text(d):
    """The tool result this hook was fired on, as text to scan."""
    if envelope(d)!='dispatch':
        return json.dumps(d.get('tool_response') or {})
    out=[str(d.get('error') or '')]
    try:
        for line in open(d['transcriptPath'],encoding='utf-8'):
            step=json.loads(line)
            if (str(step.get('step_index'))==str(d.get('stepIdx'))
                    and step.get('type')=='GENERIC'):
                out.append(str(step.get('content') or ''))
    except Exception: pass
    return '\n'.join(out)

d=json.load(sys.stdin)
shape=envelope(d)
if shape=='dispatch':
    if str(((d.get('toolCall') or {}).get('args') or {}).get('ServerName') or '')!='permitude':
        print('{}')
        sys.exit()
    root=(d.get('workspacePaths') or ['.'])[0]
else:
    root=os.environ.get('CLAUDE_PROJECT_DIR') or '.'
txt=result_text(d)
notes=[]
def ours(u):
    p=urllib.parse.urlsplit(u)
    if p.scheme=='http' and p.hostname in ('127.0.0.1','localhost','::1'): return True
    here=os.path.dirname(os.path.abspath(__file__))
    for name,key in (('.mcp.json','url'),('mcp_config.json','serverUrl')):
        try:
            m=json.load(open(os.path.join(here,'..',name),encoding='utf-8'))
            s=urllib.parse.urlsplit(next(iter(m['mcpServers'].values()))[key])
            if p.scheme=='https' and (p.scheme,p.netloc)==(s.scheme,s.netloc): return True
        except Exception: pass
    return False
def fetch(u,t):
    if not ours(u): raise ValueError('%s is not the Permitude endpoint this plugin is installed against, so nothing was fetched'%u)
    q=urllib.request.Request(u,headers={'Authorization':'Bearer '+t,'User-Agent':'permitude-plugin'})
    return urllib.request.urlopen(q,timeout=110).read()
def unpack_sdk(b):
    kit=os.path.join(root,'cadkit')
    stage=os.path.join(root,'cadkit.new')
    z=zipfile.ZipFile(io.BytesIO(b))
    bad=[n for n in z.namelist() if not n.startswith('cadkit/') or '..' in n]
    if bad: raise ValueError('unexpected archive member %r'%bad[0])
    old=''
    try: old=open(os.path.join(kit,'VERSION'),encoding='utf-8').read().strip()
    except Exception: pass
    shutil.rmtree(stage,ignore_errors=True)
    z.extractall(stage)
    shutil.rmtree(kit,ignore_errors=True)
    os.rename(os.path.join(stage,'cadkit'),kit)
    shutil.rmtree(stage,ignore_errors=True)
    new=open(os.path.join(kit,'VERSION'),encoding='utf-8').read().strip()
    if old and old!=new:
        return 'cadkit/ updated %s -> %s; git diff cadkit/ shows what changed'%(old,new)
    if old:
        return 'cadkit/ was already current (version %s)'%new
    return 'cadkit/ written (version %s)'%new
def save_seed(b):
    dest=os.path.join(root,'design_seed.py')
    fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
    try: os.write(fd,b)
    finally: os.close(fd)
    return '%s saved (%d bytes); rename it to design.py and grow the deck on it'%(dest,len(b))
def save_scene(name):
    def save(b):
        dest=os.path.join(root,name)
        json.loads(b)
        open(dest,'wb').write(b)
        return '%s saved (%d bytes); script over it, it is too large to read'%(dest,len(b))
    return save
def save_packet(b):
    dest=os.path.join(root,'permit_packet.pdf')
    open(dest,'wb').write(b)
    return '%s saved (%d bytes)'%(dest,len(b))
for m in re.finditer(r'PERMITUDE-FETCH (\S+) ([A-Za-z0-9]{32}) (permit_packet\.pdf|cadkit\.zip|design_seed\.py|scene-[0-9a-f]{8}\.json)',txt):
    name=m.group(3)
    if name=='design_seed.py' and os.path.exists(os.path.join(root,name)):
        notes.append('design_seed.py already exists, so the site seed was NOT downloaded and nothing was overwritten; move that file aside and set the site again')
        continue
    what={'permit_packet.pdf':('packet',save_packet),'cadkit.zip':('SDK',unpack_sdk),
          'design_seed.py':('site seed',save_seed)}.get(name,('scene',save_scene(name)))
    try:
        notes.append(what[1](fetch(m.group(1),m.group(2))))
    except Exception as e:
        notes.append('the %s download failed: %s'%(what[0],e))
m=re.search(r'PERMITUDE-SITE-DATA ([A-Za-z0-9_=-]+)',txt)
if m:
    try:
        raw=base64.urlsafe_b64decode(m.group(1)).decode('utf-8')
        json.loads(raw)
        pdir=os.path.join(root,'.permitude')
        os.makedirs(pdir,exist_ok=True)
        open(os.path.join(pdir,'site_data.json'),'w',encoding='utf-8').write(raw)
        notes.append('this directory is now bound to the resolved property (.permitude/site_data.json); every Permitude call here is about it')
    except Exception as e:
        notes.append('the site binding could not be recorded: %s'%e)
if shape=='dispatch':
    print('{}')
elif notes:
    print(json.dumps({'hookSpecificOutput':{'hookEventName':'PostToolUse',
                                            'additionalContext':'; '.join(notes)}}))
