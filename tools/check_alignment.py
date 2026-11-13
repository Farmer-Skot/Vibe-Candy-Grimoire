#!/usr/bin/env python3
"""Report box rows whose right edge is out of line, per piece.

Usage: python3 tools/check_alignment.py [FILE] [-v]
Rows flagged in diagrams that carry side notes are expected.
"""
import sys, re, unicodedata as U, collections
def w(s):
    n=0
    for c in s:
        cat=U.category(c)
        if cat in('Mn','Me','Cf'): continue
        n+= 2 if U.east_asian_width(c) in('W','F') else 1
    return n
L=open(sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith('-') else 'HERMETIC_CODEX',encoding='utf-8').read().split('\n')
piece=0; LEFT='┃║│'; TOP='┏╔┌╭'; BOT='┗╚└╰'; MID='┣╠├'
stats=collections.Counter(); bad=collections.defaultdict(list)
i=0
while i<len(L):
    l=L[i]
    m=re.match(r'^## PIECE (\d+)',l)
    if m: piece=int(m.group(1))
    s=l.strip()
    if s and s[0] in TOP and len(s)>4 and s[-1] in '┓╗┐╮':
        ind=len(l)-len(l.lstrip()); tw=w(l.rstrip()); j=i+1; rows=[]
        while j<len(L):
            r=L[j]; rs=r.strip()
            if not rs or (len(r)-len(r.lstrip()))!=ind or rs[0] not in LEFT+MID+BOT: break
            rows.append(j)
            if rs[0] in BOT: break
            j+=1
        stats[piece,'boxes']+=1
        for j in rows:
            if w(L[j].rstrip())!=tw: bad[piece].append((j+1,w(L[j].rstrip())-tw))
        i=j+1 if rows else i+1
        continue
    i+=1
for p in range(1,13):
    b=bad[p]; d=collections.Counter(x for _,x in b)
    print(f"piece {p:2}: boxes {stats[p,'boxes']:3}  misaligned rows {len(b):3}  offsets {dict(d)}")
if '-v' in sys.argv:
    for p in bad:
        for ln,off in bad[p][:400]: print(p,ln,off,L[ln-1])
# other checks
txt='\n'.join(L)
print("fences:",sum(1 for l in L if l.startswith('```')), " stray ''' lines:",[i+1 for i,l in enumerate(L) if l.strip()=="'''"])
print("double rules:",[i+1 for i in range(len(L)-1) if L[i]=='---' and L[i+1]=='---'])
print("trailing-space lines:",sum(1 for l in L if l!=l.rstrip()), " tabs:",sum('\t' in l for l in L))
rare=collections.Counter(c for c in txt if 0x1F700<=ord(c)<=0x1F77F or 0x13000<=ord(c)<=0x1342F)
print("alchemical/hieroglyph glyphs:",{f"U+{ord(c):X}":n for c,n in rare.items()})
print("max line width:",max(w(l) for l in L))
