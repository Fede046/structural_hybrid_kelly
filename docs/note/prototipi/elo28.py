import numpy as np
from scipy.stats import poisson
from scipy.optimize import brentq, minimize
rng=np.random.default_rng(28)

print('=== 5. Elo -> 1X2: tre mapping a confronto ===')
print(' Elo nasce a due esiti. Tre modi di ricavarne tre.')
def m_fixed(d, pdraw=0.26, ha=60, s=400):
    pw=1/(1+10**(-(d+ha)/s))
    return np.array([pw*(1-pdraw), pdraw, (1-pw)*(1-pdraw)])
def m_ologit(d, c1=-0.45, c2=0.45, beta=1.0, ha=60, s=400):
    z=beta*(d+ha)/s*np.log(10)
    F=lambda t: 1/(1+np.exp(-(t)))
    p2=F(c1-z); p1=1-F(c2-z); pX=1-p1-p2
    return np.array([p1,pX,p2])
def m_poisson(d, tot=2.7, ha=0.28, s=400):
    # differenziale Elo -> differenza di log-gol
    delta=(d/s)*np.log(10)*0.55
    lh=tot/2*np.exp((delta+ha)/2); la=tot/2*np.exp(-(delta+ha)/2)
    K=15; A=poisson.pmf(np.arange(K),lh); B=poisson.pmf(np.arange(K),la)
    P=np.outer(A,B); i,j=np.indices(P.shape)
    return np.array([P[i>j].sum(),P[i==j].sum(),P[i<j].sum()])
print(f'{"diff Elo":>9s}' + ''.join(f'{n:>26s}' for n in ['draw fisso','ordered logit','Poisson-derivato']))
print(f'{"":9s}' + '      P(1)   P(X)   P(2)'*3)
for d in [-200,-100,0,100,200,300]:
    row=''
    for f in [m_fixed,m_ologit,m_poisson]:
        p=f(d); row+=f'   {p[0]:7.4f}{p[1]:7.4f}{p[2]:7.4f}'
    print(f'{d:9d}'+row)
print(' -> il draw fisso e strutturalmente sbagliato: P(X) deve CALARE quando le squadre sono sbilanciate')
for d in [0,300]:
    print(f'    diff={d}: P(X) ologit {m_ologit(d)[1]:.4f}  Poisson {m_poisson(d)[1]:.4f}  fisso {m_fixed(d)[1]:.4f}')

print('\n=== 6. Dixon-Coles: conteggio dei parametri e vincoli ===')
for n in [20]:
    print(f' n={n} squadre: attacco {n} + difesa {n} + vantaggio casa 1 + rho 1 = {2*n+2}')
    print(f'   vincolo di identificabilita (es. media attacchi = 1, oppure somma log-alpha = 0): -1')
    print(f'   parametri liberi k = {2*n+1}')
    k=2*n+1
    for T in [380,760,1900]:
        print(f'     T={T:5d} partite -> k/T = {k/T:.4f}  (distorsione in-sample della log-verosim. ~ k/T)')

print('\n=== 7. pesatura temporale esponenziale ===')
print(' phi(t) = exp(-xi * t), t in giorni. Emivita = ln(2)/xi')
for xi in [0.0010,0.0018,0.0030,0.0050,0.0065]:
    hl=np.log(2)/xi
    print(f'   xi={xi:.4f} -> emivita {hl:6.1f} giorni = {hl/365:.2f} anni;  peso a 1 anno {np.exp(-xi*365):.3f}, a 3 anni {np.exp(-xi*365*3):.3f}')
print(' -> xi va STIMATO massimizzando la log-verosimiglianza predittiva fuori campione, non scelto')

print('\n=== 8. ordinare bene != calibrare bene ===')
N=200000
p=rng.beta(2.2,2.8,N)              # probabilita vere
y=(rng.random(N)<p).astype(float)
def auc(s,y):
    o=np.argsort(s); yy=y[o]; n1=yy.sum(); n0=len(yy)-n1
    r=np.arange(1,len(yy)+1); return (r[yy==1].sum()-n1*(n1+1)/2)/(n1*n0)
def ll(q,y): 
    q=np.clip(q,1e-9,1-1e-9); return -np.mean(y*np.log(q)+(1-y)*np.log(1-q))
def brier(q,y): return np.mean((q-y)**2)
lo=lambda x: np.log(x/(1-x)); inv=lambda z: 1/(1+np.exp(-z))
variants={'perfetto':p,
          'sovraconfidente (logit x1.6)':inv(1.6*lo(p)),
          'sottoconfidente (logit x0.6)':inv(0.6*lo(p)),
          'shift +0.5 in logit':inv(lo(p)+0.5)}
print(f'{"modello":32s}{"AUC":>9s}{"log-loss":>11s}{"Brier":>9s}{"Kelly medio":>13s}{"crescita":>12s}')
o_mkt=1/(p*1.053)   # mercato efficiente col vig
for nm,q in variants.items():
    f=np.clip((q*o_mkt-1)/(o_mkt-1),0,None)*0.25
    r=np.where(y==1,f*(o_mkt-1),-f)
    print(f'{nm:32s}{auc(q,y):9.4f}{ll(q,y):11.5f}{brier(q,y):9.5f}{f.mean():13.5f}{np.mean(np.log1p(r)):+12.3e}')
print(' -> AUC IDENTICA per tutti (trasformazioni monotone), log-loss e crescita no')
