from pathlib import Path
import hashlib,json,os,subprocess,tarfile,time,urllib.request
from huggingface_hub import snapshot_download
SPECS={
'M1':('facebook/sam2.1-hiera-tiny','de431c4043854a71d8101e17995dfe596bf101a5',None),
'M5':('BAAI/bge-small-en-v1.5','5c38ec7c405ec4b44b94cc5a9bb96e735b38267a','3c9f31665447c8911517620762200d2245a2518d6e7208acc78cd9db317e21ad'),
'M6':('cross-encoder/ms-marco-MiniLM-L-6-v2','233902d25c440f23af6f7d6e94d2946bac0bee0a','821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae'),
'M7':('openai/whisper-tiny','169d4a4341b33bc18d8881c4b69c2e104e1cc0af','7ebd0e69e78190ffe1438491fa05cc1f5c1aa3a4c4db3bc1723adbb551ea2395'),
'M8':('microsoft/Florence-2-base-ft','f6c1a25888ffc1d945ee8a1a77ac833c7303d46e','58757d657ff44051314c8030b68e04cb1bb618ca9a4885418f111f6fb708185a')}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
root=Path('work/v43/model-cache');e=Path('evidence/aura-v43-materialization');e.mkdir(parents=True,exist_ok=True)
repo=os.environ['GITHUB_REPOSITORY'];tag='aura-v43-exact-model-cache-'+os.environ['GITHUB_RUN_ID']
subprocess.run(['gh','release','create',tag,'--draft','--prerelease','--target',os.environ['GITHUB_SHA'],'--title','Exact public model cache - internal retention','--notes','Only official public model bytes and licenses. No private consumer data. Not production adoption.','--repo',repo],check=True,capture_output=True)
results=[]
for mid,(name,rev,expected) in SPECS.items():
 t=time.time();dest=root/name.replace('/','--')/rev
 rec={'model_id':mid,'model':name,'revision':rev,'expected_weight_sha256':expected,'actual_inference':False,'consumer_inputs_accessed':False,'status':'RECOVERY_RUNNING'}
 try:
  snapshot_download(name,revision=rev,local_dir=dest,allow_patterns=['*.json','*.txt','*.model','*.py','*.safetensors','README*','LICENSE*','NOTICE*','vocab.*','merges.*'],max_workers=2,token=False)
  files={p.relative_to(dest).as_posix():sha(p) for p in dest.rglob('*') if p.is_file() and '.cache' not in p.parts}
  if expected and files.get('model.safetensors')!=expected:raise ValueError('Recorded weight SHA mismatch')
  if not any(n.endswith('.safetensors') for n in files):raise ValueError('Weight bytes absent')
  (dest/'MODEL_ID.txt').write_text(name);(dest/'REVISION.txt').write_text(rev);(dest/'SHA256SUMS.txt').write_text(''.join(h+'  '+p+'\n' for p,h in sorted(files.items())))
  card=next(iter(dest.glob('README*')),None);lic=next(iter(dest.glob('LICENSE*')),None)
  if card:(dest/'MODEL_CARD.snapshot').write_bytes(card.read_bytes())
  if lic:(dest/'LICENSE.snapshot').write_bytes(lic.read_bytes())
  rec.update(status='HASH_VERIFIED',files=files,license_snapshot=bool(lic),model_card_snapshot=bool(card),license_persistence='TEST_COMPARISON_ONLY' if mid=='M5' else 'RECEIPT_REVIEW_REQUIRED')
  (dest/'MATERIALIZATION.json').write_text(json.dumps(rec,indent=2))
  archive=Path('work/v43')/(mid+'.tar.gz')
  with tarfile.open(archive,'w:gz',compresslevel=1) as tar:tar.add(dest,arcname=dest.relative_to(root),filter=lambda x:None if '/.cache/' in x.name else x)
  if archive.stat().st_size>=2_000_000_000:raise ValueError('Asset exceeds safe size limit')
  subprocess.run(['gh','release','upload',tag,str(archive),'--repo',repo],check=True,capture_output=True)
  rec.update(status='RETAINED_HASH_VERIFIED',draft_release_tag=tag,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,consumer_restore_verified=False)
 except Exception as ex:rec.update(status='RECOVERY_NOT_COMPLETE',error_type=type(ex).__name__,error=str(ex)[:1200])
 rec['elapsed_seconds']=time.time()-t;results.append(rec);(e/(mid+'.json')).write_text(json.dumps(rec,indent=2));print(mid,rec['status'],flush=True)
(e/'summary.json').write_text(json.dumps(results,indent=2))
subprocess.run(['gh','release','upload',tag,str(e/'summary.json'),'--repo',repo],check=True,capture_output=True)
