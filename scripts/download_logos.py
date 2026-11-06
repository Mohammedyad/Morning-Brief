import json, pathlib, urllib.request, urllib.parse, time
out=pathlib.Path("logos");out.mkdir(exist_ok=True)
teams=["Al Arabi SC","Al Ahli SC","Al Wakrah","Al Shahaniya","Gaziantep FK","Kasimpasa","Willem II","PEC Zwolle","Hamburger SV","Borussia Monchengladbach","Venezia","Udinese","Toulouse","Strasbourg","Sevilla","Deportivo Alaves","Everton","Coventry City","Derby County","Bolton Wanderers","Famalicao","Arouca"]
leagues=["Qatar Stars League","Turkish Super Lig","Dutch Eredivisie","German Bundesliga","Italian Serie A","French Ligue 1","Spanish La Liga","English Premier League","English League Championship","Portuguese Primeira Liga"]
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (MorningBrief/1.0)"})
    with urllib.request.urlopen(req,timeout=18) as response:
        return response.read()
def save(url,dest):
    try:
        blob=fetch(url)
        if len(blob)<100 or len(blob)>1500000:return False
        if blob[:8]==b"\\x89PNG\\r\\n\\x1a\\n" or blob[:3]==b"\\xff\\xd8\\xff" or blob[:4]==b"RIFF":
            dest.write_bytes(blob);return True
    except Exception as e:print("image error:",str(e)[:100])
    return False
for kind,names in [("team",teams),("league",leagues)]:
    for i,name in enumerate(names):
        dest=out/f"{kind}-{i}.png"
        if dest.exists():continue
        try:
            endpoint=("searchteams.php?t=" if kind=="team" else "search_all_leagues.php?c=")+urllib.parse.quote(name)
            obj=json.loads(fetch("https://www.thesportsdb.com/api/v1/json/3/"+endpoint))
            records=(obj.get("teams") or []) if kind=="team" else (obj.get("countries") or [])
            rec=next((x for x in records if x.get("strTeam" if kind=="team" else "strLeague","").lower()==name.lower()),records[0] if records else {})
            url=rec.get("strBadge") or rec.get("strLogo")
            if url and save(url,dest):print("OK",kind,name);continue
        except Exception as e:print("lookup error:",name,str(e)[:80])
        print("MISSING",kind,name)
