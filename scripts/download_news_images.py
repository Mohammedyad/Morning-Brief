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
  report.append({'index':i,'ok':False,'reason':str(e)[:140]})
(root/'assets'/'news-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
