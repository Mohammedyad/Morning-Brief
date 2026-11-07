import json, pathlib, urllib.request, urllib.parse, difflib, re, time, unicodedata, io
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
brief=json.loads((ROOT/'brief.json').read_text())
folder=ROOT/'assets'/'crests';folder.mkdir(parents=True,exist_ok=True)
codes={'eng.1':'eng.1','esp.1':'esp.1','ita.1':'ita.1','ger.1':'ger.1','fra.1':'fra.1'}
alias={'AC Milan':['milan','ac milan'],'Inter':['internazionale','inter milan'],'FC Cologne':['fc cologne','1. fc koln','koln','cologne'],'Bayer Leverkusen':['bayer leverkusen'],'Brighton':['brighton and hove albion'],'Bournemouth':['afc bournemouth'],'Atletico Madrid':['atletico madrid','atletico de madrid'],'Celta Vigo':['celta vigo','celta de vigo'],'Como':['como 1907'],'Le Mans':['le mans fc'],'Union Berlin':['1. fc union berlin'],'Schalke 04':['fc schalke 04'],'Monza':['ac monza'],'Elche':['elche cf'],'Rennes':['stade rennais'],'Lille':['losc lille'],'Marseille':['olympique de marseille'],'Lyon':['olympique lyonnais'],'Freiburg':['sc freiburg'],'Hoffenheim':['tsg hoffenheim'],'Genoa':['genoa cfc'],'Napoli':['ssc napoli'],'Lazio':['ss lazio'],'Fiorentina':['acf fiorentina'],'Juventus':['juventus fc'],'Getafe':['getafe cf'],'Villarreal':['villarreal cf'],'Levante':['levante ud'],'Rayo Vallecano':['rayo vallecano'],'Real Sociedad':['real sociedad'],'Real Betis':['real betis'],'Aston Villa':['aston villa'],'Manchester United':['manchester united'],'Crystal Palace':['crystal palace'],'Ipswich Town':['ipswich town'],'Sunderland':['sunderland'],'Chelsea':['chelsea'],'Liverpool':['liverpool'],'Brentford':['brentford'],'Atalanta':['atalanta'],'Lens':['rc lens'],'Angers':['angers sco'],'Nice':['ogc nice'],'Brest':['stade brestois'],'Lorient':['fc lorient'],'Le Havre':['le havre ac'],'Monaco':['as monaco']}
def norm(s):
 s=unicodedata.normalize('NFKD',s.lower())
 s=''.join(c for c in s if not unicodedata.combining(c))
 return re.sub(r'[^a-z0-9]+','',s)
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 MorningBrief/1.0','Accept':'application/json,image/*'})
 with urllib.request.urlopen(req,timeout=25) as r:return r.read()
def save(url,path):
 try:
  data=get(url)
  im=Image.open(io.BytesIO(data));im.load()
  if im.width<30 or im.height<30:raise ValueError('image too small')
  im.thumbnail((180,180))
  im.convert('RGBA').save(path,'PNG',optimize=True)
  return True
 except Exception as e:
  print('Image failed',url,str(e)[:130]);return False
def teamlist(code):
 url=f'https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams?limit=1000'
 data=json.loads(get(url))
 sports=data.get('sports',[])
 teams=[]
 for sport in sports:
  for league in sport.get('leagues',[]):
   for entry in league.get('teams',[]):
    t=entry.get('team',entry)
    names=[t.get('displayName',''),t.get('name',''),t.get('shortDisplayName',''),t.get('abbreviation','')]
    logos=t.get('logos',[])
    if logos:teams.append((names,logos[0].get('href','')))
 return teams
def choose(name,teams):
 choices=[norm(name)]+[norm(x) for x in alias.get(name,[])]
 for names,url in teams:
  if any(norm(n) in choices for n in names if n):return url
 scored=[]
 for names,url in teams:
  score=max([difflib.SequenceMatcher(None,x,norm(n)).ratio() for x in choices for n in names if n] or [0])
  scored.append((score,url,names[0]))
 scored.sort(reverse=True)
 if scored and scored[0][0]>.82:return scored[0][1]
 print('NO MATCH',name,scored[:2]);return None
report={'success':[],'missing':[],'league_success':[]}
for code in sorted(set(m['espn'] for m in brief['matches'])):
 try:teams=teamlist(code);print('ESPN',code,len(teams))
 except Exception as e:print('ESPN unavailable',code,e);teams=[]
 names=sorted(set(v for m in brief['matches'] if m['espn']==code for v in [m['home'],m['away']]))
 for name in names:
  slug=norm(name);dest=folder/(code+'-'+slug+'.png')
  if dest.exists():report['success'].append(name);continue
  url=choose(name,teams)
  if url and save(url,dest):report['success'].append(name);continue
  # backup provider: TheSportsDB official team badge URL
  try:
   data=json.loads(get('https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t='+urllib.parse.quote(name)))
   rec=next((t for t in (data.get('teams') or []) if t.get('strSport')=='Soccer'),None)
   if rec and rec.get('strBadge') and save(rec['strBadge'],dest):report['success'].append(name);continue
  except Exception as e:print('Backup failed',name,str(e)[:90])
  report['missing'].append(name)
# League emblems from ESPN league logo CDN, verified by league code
for code in codes:
 dest=folder/('league-'+code+'.png')
 for url in [f'https://a.espncdn.com/i/leaguelogos/soccer/500/{code}.png',f'https://a.espncdn.com/i/leaguelogos/soccer/500-dark/{code}.png']:
  if save(url,dest):report['league_success'].append(code);break
# Verified league emblems from Wikimedia article thumbnail metadata when ESPN league CDN is unavailable
wiki_titles={'eng.1':'Premier_League','esp.1':'La_Liga','ita.1':'Serie_A','ger.1':'Bundesliga','fra.1':'Ligue_1'}
for code,title in wiki_titles.items():
 dest=folder/('league-'+code+'.png')
 if dest.exists():continue
 try:
  api='https://en.wikipedia.org/w/api.php?action=query&format=json&prop=pageimages&piprop=thumbnail&pithumbsize=300&titles='+urllib.parse.quote(title)
  obj=json.loads(get(api))
  pages=obj.get('query',{}).get('pages',{})
  for p in pages.values():
   url=p.get('thumbnail',{}).get('source')
   if url and save(url,dest):
    report['league_success'].append(code);break
 except Exception as e:print('Wikimedia failed',code,str(e)[:100])
# Commons files are specifically identified as league marks (not generic page photos).
commons_files={'eng.1':'Pl-logo-light.svg','esp.1':'LaLiga logo 2023.svg','ita.1':'Serie A.svg','ger.1':'Bundesliga logo.svg','fra.1':"Ligue 1 McDonald's logo.svg"}
for code,filename in commons_files.items():
 dest=folder/('league-'+code+'.png')
 if dest.exists():continue
 try:
  q=urllib.parse.urlencode({'action':'query','format':'json','prop':'imageinfo','iiprop':'url','iiurlwidth':'240','titles':'File:'+filename})
  obj=json.loads(get('https://commons.wikimedia.org/w/api.php?'+q))
  pages=obj.get('query',{}).get('pages',{})
  for page in pages.values():
   for info in page.get('imageinfo',[]):
    url=info.get('thumburl')
    if url and save(url,dest):
     report['league_success'].append(code);break
 except Exception as e:print('Commons logo failed',code,str(e)[:120])
# ESPN scoreboard league metadata provides directly attributed league logos.
for code in codes:
 dest=folder/('league-'+code+'.png')
 if dest.exists():continue
 try:
  obj=json.loads(get('https://site.api.espn.com/apis/site/v2/sports/soccer/'+code+'/scoreboard?dates=20261108'))
  for lg in obj.get('leagues',[]):
   for image in lg.get('logos',[]):
    if image.get('href') and save(image['href'],dest):
     report['league_success'].append(code);break
 except Exception as e:print('ESPN league metadata failed',code,str(e)[:100])
(ROOT/'assets'/'logo-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('RESULT',json.dumps(report,ensure_ascii=False))
