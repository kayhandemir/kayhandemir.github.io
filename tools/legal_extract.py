# Pull the legal text out of the old pages as clean HTML (tags kept, classes/styles dropped).
import re, sys, html
from html.parser import HTMLParser
KEEP = {'h2','h3','h4','p','ul','ol','li','table','thead','tbody','tr','th','td','a','strong','em','b','i','br'}
VOID = {'br'}
class S(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True); s.out=[]; s.skip=0; s.on=False; s.depth=0
    def handle_starttag(s,t,a):
        if t in ('script','style','svg','button','form','nav','footer'): s.skip+=1; return
        if s.skip: return
        if t=='h1': s.on=True; s.in_h1=True; return
        if not s.on: return
        if t in KEEP:
            if t=='a':
                href=dict(a).get('href','')
                s.out.append(f'<a href="{html.escape(href)}">')
            else: s.out.append(f'<{t}>')
    def handle_endtag(s,t):
        if t in ('script','style','svg','button','form','nav','footer'): s.skip-=1; return
        if s.skip: return
        if t=='h1': s.in_h1=False; return
        if t=='main': s.on=False
        if s.on and t in KEEP and t not in VOID: s.out.append(f'</{t}>')
    def handle_data(s,d):
        if s.skip or not s.on or getattr(s,'in_h1',False): return
        s.out.append(html.escape(d))
def extract(path):
    p=S(); p.feed(open(path,encoding='utf-8').read())
    h=''.join(p.out)
    h=re.sub(r'\s+',' ',h)
    h=re.sub(r'<(p|li|h[2-4]|td|th|strong|a[^>]*)>\s+',r'<\1>',h)
    h=re.sub(r'\s+</(p|li|h[2-4]|td|th|strong|a)>',r'</\1>',h)
    for _ in range(3): h=re.sub(r'<(p|strong|em|b|i|li|ul)>\s*</\1>','',h)
    h=re.sub(r'\s*(<(h[2-4]|p|ul|ol|li|table|thead|tbody|tr)>)',r'\n\1',h)
    h=re.sub(r'\s*(</(ul|ol|table|thead|tbody|tr)>)',r'\n\1',h)
    h=re.sub(r'\s+(</(p|li|h[2-4]|td|th)>)',r'\1',h)
    return h.strip()
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8'); print(extract(sys.argv[1]))
