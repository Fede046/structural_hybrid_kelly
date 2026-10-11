import numpy as np
rng=np.random.default_rng(2025)
print('=== 1. Varianza della singola puntata: f^2 b^2 p(1-p) oppure f^2 o^2 p(1-p)? ===')
print(f'{"p":>6s}{"o":>6s}{"b":>6s}{"f":>6s}{"Var empirica":>15s}{"f^2 b^2 p(1-p)":>17s}{"f^2 o^2 p(1-p)":>17s}')
for p,o,f in [(0.55,2.00,0.10),(0.16,6.50,0.02),(0.40,2.70,0.05),(0.70,1.50,0.20)]:
    b=o-1; N=4_000_000
    win=rng.random(N)<p
    r=np.where(win, f*b, -f)
    v=r.var()
    print(f'{p:6.2f}{o:6.2f}{b:6.2f}{f:6.2f}{v:15.8f}{f**2*b**2*p*(1-p):17.8f}{f**2*o**2*p*(1-p):17.8f}')
print(' -> la formula corretta usa o = b+1, non b.  Var(X) = (range)^2 p(1-p) con range = b-(-1) = o')
print()
print('=== 2. Portafoglio: correlazioni reali ===')
N=2_000_000
# (a) due scommesse su PARTITE DIVERSE, esiti indipendenti
p1,o1,f1=0.45,2.30,0.04; p2,o2,f2=0.38,2.80,0.03
r1=np.where(rng.random(N)<p1, f1*(o1-1), -f1)
r2=np.where(rng.random(N)<p2, f2*(o2-1), -f2)
print(f' partite diverse, esiti indipendenti: corr(r1,r2) = {np.corrcoef(r1,r2)[0,1]:+.5f}')
# (b) due esiti dello STESSO match (1 e X)
p=np.array([0.45,0.27,0.28]); o=np.array([2.10,3.50,3.40]); f=np.array([0.04,0.03,0.0])
y=(rng.random(N)[:,None]>p.cumsum()).sum(1)
ra=np.where(y==0, f[0]*(o[0]-1), -f[0])
rb=np.where(y==1, f[1]*(o[1]-1), -f[1])
print(f' stesso match, esiti 1 e X:           corr = {np.corrcoef(ra,rb)[0,1]:+.5f}')
print(f'   formula teorica -sqrt(p1 p2/((1-p1)(1-p2))) = {-np.sqrt(p[0]*p[1]/((1-p[0])*(1-p[1]))):+.5f}')
print(' -> stesso match: correlazione NEGATIVA forte (esiti mutuamente esclusivi), non "positiva forte"')
