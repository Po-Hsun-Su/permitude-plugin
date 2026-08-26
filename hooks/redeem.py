import json,sys,re,io,os,shutil,zipfile,base64,urllib.request
d=json.load(sys.stdin)
txt=json.dumps(d.get('tool_response') or {})
root=os.environ.get('CLAUDE_PROJECT_DIR') or '.'
notes=[]
m=re.search(r'PERMITUDE-PACKET-FETCH (\S+) ([A-Za-z0-9]{32})',txt)
if m:
    try:
        dest=os.path.join(root,'permit_packet.pdf')
        q=urllib.request.Request(m.group(1),headers={'Authorization':'Bearer '+m.group(2),'User-Agent':'permitude-plugin'})
        b=urllib.request.urlopen(q,timeout=110).read()
        open(dest,'wb').write(b)
        notes.append('%s saved (%d bytes)'%(dest,len(b)))
    except Exception as e:
        notes.append('the packet download failed: %s'%e)
m=re.search(r'PERMITUDE-SDK-FETCH (\S+) ([A-Za-z0-9]{32})',txt)
if m:
    try:
        kit=os.path.join(root,'cadkit')
        stage=os.path.join(root,'cadkit.new')
        q=urllib.request.Request(m.group(1),headers={'Authorization':'Bearer '+m.group(2),'User-Agent':'permitude-plugin'})
        b=urllib.request.urlopen(q,timeout=110).read()
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
            notes.append('cadkit/ updated %s -> %s; git diff cadkit/ shows what changed'%(old,new))
        elif old:
            notes.append('cadkit/ was already current (version %s)'%new)
        else:
            notes.append('cadkit/ written (version %s)'%new)
    except Exception as e:
        notes.append('the SDK download failed: %s'%e)
m=re.search(r'PERMITUDE-SEED-FETCH (\S+) ([A-Za-z0-9]{32})',txt)
if m:
    dest=os.path.join(root,'design_seed.py')
    if os.path.exists(dest):
        notes.append('design_seed.py already exists, so the site seed was NOT downloaded and nothing was overwritten; move that file aside and call site_context again')
    else:
        try:
            q=urllib.request.Request(m.group(1),headers={'Authorization':'Bearer '+m.group(2),'User-Agent':'permitude-plugin'})
            b=urllib.request.urlopen(q,timeout=110).read()
            fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
            try: os.write(fd,b)
            finally: os.close(fd)
            notes.append('%s saved (%d bytes); rename it to design.py and grow the deck on it'%(dest,len(b)))
        except Exception as e:
            notes.append('the site seed download failed: %s'%e)
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
if notes:
    print(json.dumps({'hookSpecificOutput':{'hookEventName':'PostToolUse','additionalContext':'; '.join(notes)}}))
