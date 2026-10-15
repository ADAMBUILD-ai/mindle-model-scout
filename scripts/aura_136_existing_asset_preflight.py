"""Read/hash existing pinned assets only; no torch import, weights load or inference."""
import argparse, importlib.metadata, json, platform, socket, sys, time
from pathlib import Path
from run_aura_136_local_benchmark import digest, verify_model
MODEL_ID='Qwen/Qwen3-4B'
REVISION='1cfa9a7208912126459214e8b04321603b3df60c'
def inspect_existing(root, manifest):
    if manifest.get('modelId')!=MODEL_ID or manifest.get('revision')!=REVISION:
        raise ValueError('HANDOVER_MODEL_MISMATCH')
    root=verify_model(root,manifest,require_inference_approval=False)
    if 'LICENSE' not in {x['path'] for x in manifest['files']}:
        raise ValueError('PINNED_LICENSE_FILE_REQUIRED')
    versions={}
    for name in ('torch','transformers'):
        try:versions[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:versions[name]=None
    return {'status':'READ_ONLY_LOCAL_FILES_VERIFIED',
            'observedAtUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
            'modelId':MODEL_ID,'revision':REVISION,'modelRoot':str(root),
            'fileCount':len(manifest['files']),'totalBytes':sum(x['bytes'] for x in manifest['files']),
            'manifestFiles':manifest['files'],'pythonExe':sys.executable,
            'pythonExeSha256':digest(sys.executable),'pythonVersion':platform.python_version(),
            'hostName':socket.gethostname(),'platform':platform.platform(),'machine':platform.machine(),
            'runtimePackageMetadata':versions,'runtimeImportsExecuted':False,
            'runtimeSuitableVerified':False,'sameHostAsAcquisitionVerified':False,
            'licenseApproved':False,'weightsLoaded':False,'modelCalls':0,
            'installationExecuted':False,'inferenceReleased':False,'productPass':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--model-root',required=True)
    p.add_argument('--manifest',required=True);p.add_argument('--receipt',required=True)
    a=p.parse_args();out=Path(a.receipt)
    # Reserve a new receipt before long hashing; never overwrite existing evidence.
    with out.open('x',encoding='utf-8') as f:
        f.write(json.dumps({'status':'READ_ONLY_HASH_STARTED','modelCalls':0})+'\n')
    try:
        m=json.loads(Path(a.manifest).read_text(encoding='utf-8-sig'))
        r=inspect_existing(a.model_root,m);r['manifestFileSha256']=digest(a.manifest)
        code=0
    except Exception as e:
        r={'status':'READ_ONLY_HANDOVER_BLOCKED','error':type(e).__name__+': '+str(e),
           'modelCalls':0,'weightsLoaded':False,'inferenceReleased':False,'productPass':False}
        code=2
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':r['status'],'modelCalls':0}));return code
if __name__=='__main__':raise SystemExit(main())
