import json,os,sys
d=json.load(sys.stdin)
i=dict(d.get('tool_input') or {})
n=str(d.get('tool_name') or '')
root=os.environ.get('CLAUDE_PROJECT_DIR') or '.'
if n.endswith('deck_build'):
    p=i.pop('path','')
    i['path_read']=p
    try: i['source']=open(p,encoding='utf-8').read()
    except Exception: i['source']=''
    try: i['sdk_version']=open(os.path.join(os.path.dirname(os.path.abspath(p)),'cadkit','VERSION'),encoding='utf-8').read().strip()
    except Exception: pass
try: i['site_data']=open(os.path.join(root,'.permitude','site_data.json'),encoding='utf-8').read()
except Exception: pass
print(json.dumps({'hookSpecificOutput':{'hookEventName':'PreToolUse','updatedInput':i}}))
