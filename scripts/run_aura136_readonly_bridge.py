"""Read-only bridge for acquisition receipts and AURA's frozen preflight."""
import hashlib,json,os,sys,time
from pathlib import Path
from aura_136_existing_asset_preflight import inspect_existing
from run_aura_136_local_benchmark import digest

def project_manifest(source, config):
    if source.get('modelId') != 'Qwen/Qwen3-4B' or source.get('revision') != '1cfa9a7208912126459214e8b04321603b3df60c':
        raise ValueError('ACQUISITION_IDENTITY_MISMATCH')
    if not any('CausalLM' in x for x in config.get('architectures', [])):
        raise ValueError('CONFIG_NOT_CAUSAL_LM')
    if source.get('licenseSnapshotSha256') != '832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e':
        raise ValueError('PINNED_LICENSE_MISMATCH')
    return {'modelId':source['modelId'],'revision':source['revision'],'family':'causal-lm','files':source['files'],'approvedDesktopInference':False}

def main():
    root=Path(r'C:\actions-runner\_work\_state\mindle-model-scout\aura136-pinned-models\Qwen--Qwen3-4B\1cfa9a7208912126459214e8b04321603b3df60c')
    manifest=root.parent/'AURA136_MODEL_MANIFEST_1cfa9a7208912126459214e8b04321603b3df60c.json'
    out=Path('aura136-existing-asset-preflight-'+os.environ['GITHUB_RUN_ID']+'.json')
    with out.open('x',encoding='utf-8') as f:f.write('{"status":"READ_ONLY_HASH_STARTED","modelCalls":0}\n')
    started=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    code=2
    try:
        source=json.loads(manifest.read_text(encoding='utf-8-sig'))
        config=json.loads((root/'config.json').read_text(encoding='utf-8'))
        projected=project_manifest(source,config)
        result=inspect_existing(root,projected)
        result['sourceManifestSha256']=digest(manifest)
        result['sourceManifestPath']=str(manifest)
        result['schemaBridge']='family derived from existing config architectures; source manifest unchanged'
        result['projectedManifestCanonicalSha256']=hashlib.sha256(json.dumps(projected,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        code=0
    except Exception as error:
        result={'status':'READ_ONLY_HANDOVER_BLOCKED','error':type(error).__name__+': '+str(error),'modelCalls':0,'weightsLoaded':False,'inferenceReleased':False,'productPass':False}
    result.update({'startedAtUTC':started,'finishedAtUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'exitCode':code,'command':sys.executable+' scripts/run_aura136_readonly_bridge.py','runId':os.environ['GITHUB_RUN_ID'],'sourceCommit':os.environ['GITHUB_SHA'],'executionContext':'GitHub Actions self-hosted service; owner desktop access NOT verified','frozenAuraCommit':'26836b5cfed9b434a42181d7e5101897c0aa5f7a'})
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':str(out),'receiptSha256':digest(out),'status':result['status'],'modelCalls':0,'exitCode':code}))
    return code
if __name__=='__main__':raise SystemExit(main())
