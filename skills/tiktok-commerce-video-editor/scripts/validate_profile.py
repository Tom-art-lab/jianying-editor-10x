#!/usr/bin/env python3
"""Small, dependency-free validator for portable project profiles."""
import json, sys
from pathlib import Path

def fail(message):
    raise SystemExit(f"INVALID: {message}")

def main(path):
    p=Path(path)
    try: data=json.loads(p.read_text(encoding='utf-8'))
    except Exception as e: fail(f"cannot read JSON: {e}")
    for key in ('schema_version','project_name','canvas','roles','allowed_orders','caption','audio','delivery'):
        if key not in data: fail(f"missing {key}")
    c=data['canvas']
    if not all(isinstance(c.get(k),(int,float)) and c[k]>0 for k in ('width','height','fps')): fail('canvas must have positive width/height/fps')
    roles=data['roles']
    ids=[r.get('id') for r in roles if isinstance(r,dict)]
    if len(ids)!=len(roles) or any(not x or not isinstance(x,str) for x in ids): fail('roles require string ids')
    if len(set(ids))!=len(ids): fail('duplicate role id')
    allowed=data['allowed_orders']
    if not isinstance(allowed,list) or not allowed: fail('allowed_orders must be non-empty list')
    role_set=set(ids)
    for order in allowed:
        if not isinstance(order,list) or not order: fail('each allowed order must be non-empty list')
        if any(x not in role_set for x in order): fail(f'order references unknown role: {order}')
        if len(set(order))!=len(order): fail(f'order repeats a role: {order}')
    cap=data['caption']; rect=cap.get('safe_rect',{})
    if cap.get('max_lines',0)>2: fail('caption max_lines cannot exceed 2')
    if not all(isinstance(rect.get(k),(int,float)) and rect[k]>=0 for k in ('x','y','w','h')): fail('caption safe_rect invalid')
    if rect['x']+rect['w']>c['width'] or rect['y']+rect['h']>c['height']: fail('caption safe_rect outside canvas')
    if cap.get('composite_last') is not True: fail('captions must be composited last')
    audio=data['audio']
    if audio.get('retain_source_audio') is not True: fail('retain_source_audio must be true')
    if audio.get('music_policy') not in ('prompt_user_folder','skip','optional'):
        fail('audio.music_policy must be prompt_user_folder, skip, or optional')
    if audio.get('music_policy') != 'skip' and not isinstance(audio.get('music_dir'),str):
        fail('audio.music_dir is required unless music_policy is skip')
    arrow=data.get('cta_arrow',{})
    if arrow.get('enabled'):
        shape=str(arrow.get('shape','')).lower()
        if 'thick' not in shape or 'triangular' not in shape: fail('enabled arrow needs thick shaft and triangular head')
    if data['delivery'].get('mp4_only') is not True: fail('delivery.mp4_only must be true')
    print(json.dumps({'valid':True,'project_name':data['project_name'],'roles':len(ids),'orders':len(allowed)},ensure_ascii=False))

if __name__=='__main__':
    if len(sys.argv)!=2: raise SystemExit('usage: validate_profile.py path/to/profile.json')
    main(sys.argv[1])
