import json,pathlib,urllib.request,urllib.parse,re,html,io
from html.parser import HTMLParser
from PIL import Image
root=pathlib.Path(__file__).resolve().parents[1]
brief=json.loads((root/'brief.json').read_text())
out=root/'assets'/'news';out.mkdir(parents=True,exist_ok=True)
class Meta(HTMLParser):
 def __init__(self):super().__init__();self.tags={}
 def handle_starttag(self,tag,attrs):
  if tag!='meta':return
  a=dict(attrs);key=a.get('property',a.get('name','')).lower()
  if key in ('og:image','twitter:image','twitter:image:src') and a.get('content'):self.tags[key]=html.unescape(a['content'])
def fetch(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; MorningBriefNews/1.0)','Accept':'text/html,image/*'})
 with urllib.request.urlopen(req,timeout=22) as r:return r.read(),r.geturl()
fallback_photos={0:'https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?w=1100&q=82',1:'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1100&q=82',2:'https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1100&q=82',3:'https://images.unsplash.com/photo-1590283603385-17ffb3a7f29f?w=1100&q=82',4:'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1100&q=82'}
report=[]
for i,story in enumerate(brief['news']):
 dest=out/f'story-{i}.jpg'
 if dest.exists() and dest.stat().st_size>1000:
  report.append({'index':i,'ok':True,'cached':True});continue
 try:
  content,final=fetch(story['url']);parser=Meta();parser.feed(content[:900000].decode('utf-8','ignore'))
  src=parser.tags.get('og:image') or parser.tags.get('twitter:image') or parser.tags.get('twitter:image:src')
  if not src:raise ValueError('No publisher OG image')
  src=urllib.parse.urljoin(final,src)
  raw,_=fetch(src)
  im=Image.open(io.BytesIO(raw));im.load()
  if im.width<350 or im.height<180:raise ValueError('Source image too small')
  im=im.convert('RGB');im.thumbnail((1100,700));im.save(dest,'JPEG',quality=83,optimize=True)
  report.append({'index':i,'ok':True,'source':src,'size':len(raw)})
 except Exception as e:
  try:
   raw,_=fetch(fallback_photos[i])
   im=Image.open(io.BytesIO(raw));im.load()
   if im.width<350:raise ValueError('Fallback too small')
   im=im.convert('RGB');im.thumbnail((1100,700));im.save(dest,'JPEG',quality=83,optimize=True)
   report.append({'index':i,'ok':True,'illustrative':True,'source':fallback_photos[i]})
  except Exception as e2:
   report.append({'index':i,'ok':False,'reason':str(e)[:100]+'; '+str(e2)[:100]})
(root/'assets'/'news-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
