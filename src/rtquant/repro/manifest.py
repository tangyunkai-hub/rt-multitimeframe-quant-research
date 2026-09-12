from pathlib import Path
import hashlib, json

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def build_manifest(*,run_id,files,metadata=None):
    payload={'run_id':run_id,'files':{str(Path(p).name):sha256_file(p) for p in files},'metadata':metadata or {}}
    payload['manifest_sha256']=hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
    return payload
