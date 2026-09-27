"""Permitude's post-tool hook. It spends what a Permitude result hands back:
one fetch line names a file from a closed set — the permit packet, the
Permitude reference copy it unpacks into ``cadkit/``, this property's starter
design, one build's scene — and one binding line records which property this
folder is bound to. The hook carries every byte and every credential, so
nothing the agent types has to.

A result can quote text other people wrote — a note left in the viewer, a
design someone shared — so the hook acts only on lines the Permitude server
itself wrote, and it tells them apart by where they sit. What it refuses:

- **Any other server's result**, and any Permitude result other than the four
  calls that hand back a file or a binding (``HANDS_BACK``), whatever it
  contains.
- **Any line that does not open the result.** The lines acted on are the
  first lines of the result's first block, before any other text; a line
  anywhere after that is quoted text and is ignored.
- **A file name the call does not hand back.** Each call names its own.
- **Any address but the one this plugin is configured for.** A fetch goes
  only to the scheme, host and port the plugin's own server entry names —
  https, or plain http to this machine at the port a developer running a
  local server wrote there — and never follows a redirect, so the credential
  it presents reaches no one else.

Where it writes is the folder the agent is working in, read the way
``carry.py`` reads it.
"""
import json,sys,re,io,os,shutil,zipfile,base64,urllib.request,urllib.parse

SERVER='permitude'
HANDS_BACK={
    ('read_reference','sdk'):r'cadkit\.zip',
    ('read_project','packet'):r'permit_packet\.pdf',
    ('read_project','scene'):r'scene-[0-9a-f]{8}\.json',
    ('set_project','site'):r'design_seed\.py',
}
BINDS=('set_project','site')

def envelope(d):
    """Which hook protocol this payload arrived on, as the one thing that
    differs between the agents Permitude supports: where the tool's result is
    to be found, and what the hook may answer with.

    ``replace`` — Claude Code and Codex CLI. Events ``PreToolUse`` and
    ``PostToolUse``; the call's arguments arrive as ``tool_input`` and its
    result whole as ``tool_response``, and the answer is a sentence for the
    agent, ``additionalContext``, naming its own event beside it.
    https://docs.claude.com/en/docs/claude-code/hooks
    https://learn.chatgpt.com/docs/hooks

    ``dispatch`` — Antigravity CLI. Every MCP call is one dispatcher tool
    named ``call_mcp_tool``; the payload carries the call under ``toolCall``,
    the step's number as ``stepIdx``, ``error`` when the call failed, and no
    result at all when it succeeded. The result text is in the transcript
    file the payload names, one JSON object per line, and the object for this
    step is the one whose ``step_index`` is that number and whose ``type`` is
    ``GENERIC``: reading it by step is what keeps a hook from redeeming a
    line some earlier call left behind. That text opens with the step's own
    ``Created At:`` and ``Completed At:`` lines, then the result's blocks
    joined by line breaks. The only answer this event takes is an empty
    object, so an Antigravity session is told what landed by the tool's own
    result rather than by this hook. Measured against Antigravity CLI 1.1.28.
    https://antigravity.google/docs/cli
    """
    return 'dispatch' if 'toolCall' in d else 'replace'

def permitude_call(d):
    """The Permitude tool this result came from and the ``what`` it was
    called with, or ``None`` for a result from any other server. The server
    is named the way ``carry.py`` reads it."""
    if envelope(d)=='dispatch':
        call=(d.get('toolCall') or {}).get('args') or {}
        server,tool,args=call.get('ServerName'),call.get('ToolName'),call.get('Arguments')
    else:
        m=re.fullmatch(r'mcp__(?:plugin_permitude_)?(permitude)__([a-z_]+)',str(d.get('tool_name') or ''))
        server,tool,args=(m.group(1),m.group(2),d.get('tool_input')) if m else (None,None,None)
    if server!=SERVER or not isinstance(args,dict):
        return None
    return str(tool),str(args.get('what') or '')

def workspace(d):
    """The folder the agent is working in, or ``None`` when it named none."""
    if envelope(d)=='dispatch':
        return (d.get('workspacePaths') or [None])[0]
    return os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd()

def opening(d):
    """The text the result opens with — its first block — in whichever shape
    the agent hands it over: the result object, its list of blocks, or the
    transcript line of this step."""
    if envelope(d)=='dispatch':
        try:
            for line in open(d['transcriptPath'],encoding='utf-8'):
                step=json.loads(line)
                if (str(step.get('step_index'))==str(d.get('stepIdx'))
                        and step.get('type')=='GENERIC'):
                    text=str(step.get('content') or '')
                    return re.sub(r'\A(?:(?:Created|Completed) At: [^\n]*\n)*','',text)
        except Exception: pass
        return ''
    r=d.get('tool_response')
    if isinstance(r,dict): r=r.get('content')
    if isinstance(r,list): r=r[0].get('text') if r and isinstance(r[0],dict) else None
    return r if isinstance(r,str) else ''

def head(text):
    """The ``PERMITUDE-`` lines the text opens with, up to the first line
    that is anything else."""
    lines=[]
    for line in text.split('\n'):
        if not line.startswith('PERMITUDE-'): break
        lines.append(line)
    return lines

def trusted(u):
    """Whether ``u`` is on the one server this plugin is configured for."""
    p=urllib.parse.urlsplit(u)
    here=os.path.dirname(os.path.abspath(__file__))
    for name,key in (('.mcp.json','url'),('mcp_config.json','serverUrl')):
        try:
            with open(os.path.join(here,'..',name),encoding='utf-8') as f:
                s=urllib.parse.urlsplit(json.load(f)['mcpServers'][SERVER][key])
        except Exception: continue
        local=s.scheme=='http' and s.hostname in ('127.0.0.1','localhost','::1')
        if (s.scheme=='https' or local) and (p.scheme,p.netloc)==(s.scheme,s.netloc): return True
    return False

class Stay(urllib.request.HTTPRedirectHandler):
    """A redirect is refused, never followed."""
    def redirect_request(self,*args,**kwargs): return None

def fetch(u,t):
    if not trusted(u): raise ValueError('%s is not the Permitude endpoint this plugin is installed against, so nothing was fetched'%u)
    q=urllib.request.Request(u,headers={'Authorization':'Bearer '+t,'User-Agent':'permitude-plugin'})
    return urllib.request.build_opener(Stay).open(q,timeout=110).read()
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
def redeem(line,names):
    m=re.fullmatch(r'PERMITUDE-FETCH (\S+) ([A-Za-z0-9]{32}) (%s)'%names,line)
    if not m: return
    name=m.group(3)
    if name=='design_seed.py' and os.path.exists(os.path.join(root,name)):
        notes.append('design_seed.py already exists, so the site seed was NOT downloaded and nothing was overwritten; move that file aside and set the site again')
        return
    what={'permit_packet.pdf':('packet',save_packet),'cadkit.zip':('SDK',unpack_sdk),
          'design_seed.py':('site seed',save_seed)}.get(name,('scene',save_scene(name)))
    try:
        notes.append(what[1](fetch(m.group(1),m.group(2))))
    except Exception as e:
        notes.append('the %s download failed: %s'%(what[0],e))
def bind(line):
    m=re.fullmatch(r'PERMITUDE-SITE-DATA ([A-Za-z0-9_=-]+)',line)
    if not m: return
    try:
        raw=base64.urlsafe_b64decode(m.group(1)).decode('utf-8')
        json.loads(raw)
        pdir=os.path.join(root,'.permitude')
        os.makedirs(pdir,exist_ok=True)
        open(os.path.join(pdir,'site_data.json'),'w',encoding='utf-8').write(raw)
        notes.append('this directory is now bound to the resolved property (.permitude/site_data.json); every Permitude call here is about it')
    except Exception as e:
        notes.append('the site binding could not be recorded: %s'%e)

d=json.load(sys.stdin)
call=permitude_call(d)
root=workspace(d)
notes=[]
if call in HANDS_BACK and root:
    for line in head(opening(d)):
        redeem(line,HANDS_BACK[call])
        if call==BINDS:
            bind(line)
if envelope(d)=='dispatch':
    print('{}')
elif notes:
    print(json.dumps({'hookSpecificOutput':{'hookEventName':'PostToolUse',
                                            'additionalContext':'; '.join(notes)}}))
