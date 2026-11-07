import json,pathlib,re
root=pathlib.Path(__file__).resolve().parents[1]
data=json.loads((root/'brief.json').read_text())
report=json.loads((root/'assets/logo-report.json').read_text())
html=(root/'index.html').read_text()
def slug(s):
 import unicodedata
 s=unicodedata.normalize('NFKD',s.lower())
 s=''.join(c for c in s if not unicodedata.combining(c))
 return re.sub(r'[^a-z0-9]','',s)
missing=[]
for m in data['matches']:
 for t in ('home','away'):
  p=root/'assets/crests'/(m['espn']+'-'+slug(m[t])+'.png')
  if not p.exists() or p.stat().st_size<100:missing.append(str(p))
for code in sorted(set(m['espn'] for m in data['matches'])):
 p=root/'assets/crests'/('league-'+code+'.png')
 if not p.exists() or p.stat().st_size<100:missing.append(str(p))
assert len(data['matches'])==24,len(data['matches'])
assert len(data['news'])>=5,len(data['news'])
assert data['matches']==sorted(data['matches'],key=lambda m:m['time'])
assert 'news-tab' in html and 'sports-tab' in html
assert 'const data=' in html
assert not missing,missing
result={'date':data['dateISO'],'matches':len(data['matches']),'news':len(data['news']),'teams':len(set((m['espn'],m[k]) for m in data['matches'] for k in ['home','away'])),'competitions':len(set(m['espn'] for m in data['matches'])),'missing_images':missing,'passed':True}
(root/'assets/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
