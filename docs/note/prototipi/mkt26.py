import numpy as np
from scipy.stats import poisson
np.set_printoptions(precision=4,suppress=True)

print('=== 1. Overround nell esempio del paper (Burnley-Man City, 11/08/2023) ===')
x=np.array([8.0,5.5,1.33]); ou=np.array([1.67,2.20])
print(f' 1X2  quote {x}  booksum {np.sum(1/x):.6f}  Omega {(np.sum(1/x)-1)*100:.3f}%')
print(f' O/U  quote {ou}  booksum {np.sum(1/ou):.6f}  Omega {(np.sum(1/ou)-1)*100:.3f}%')
print(f' EV dichiarato dall agente su home: 0.401*8-1 = {0.401*8-1:+.4f} -> "edge 220.7%" e in realta EV')

print('\n=== 2. 1X2 e Over/Under partizionano lo STESSO spazio: correlazione ===')
def joint(lh,la,K=12):
    A=poisson.pmf(np.arange(K),lh); B=poisson.pmf(np.arange(K),la)
    return np.outer(A,B)
def stats(lh,la):
    P=joint(lh,la); K=P.shape[0]
    i,j=np.indices(P.shape)
    home=(i>j); draw=(i==j); away=(i<j); over=((i+j)>2.5)
    ph,pd,pa,po=P[home].sum(),P[draw].sum(),P[away].sum(),P[over].sum()
    def corr(m1,m2):
        p1=P[m1].sum(); p2=P[m2].sum(); p12=P[m1&m2].sum()
        return (p12-p1*p2)/np.sqrt(p1*(1-p1)*p2*(1-p2))
    return ph,pd,pa,po,corr(home,over),corr(draw,over),corr(away,over)
print(f'{"lam_h":>7s}{"lam_a":>7s}{"P(1)":>8s}{"P(X)":>8s}{"P(2)":>8s}{"P(O2.5)":>9s}{"corr(1,O)":>11s}{"corr(X,O)":>11s}{"corr(2,O)":>11s}')
for lh,la in [(1.53,1.18),(2.40,0.70),(0.80,2.20),(1.10,1.05),(2.00,1.80)]:
    s=stats(lh,la)
    print(f'{lh:7.2f}{la:7.2f}{s[0]:8.4f}{s[1]:8.4f}{s[2]:8.4f}{s[3]:9.4f}{s[4]:+11.4f}{s[5]:+11.4f}{s[6]:+11.4f}')
print(' -> il PAREGGIO e fortemente correlato NEGATIVAMENTE con Over 2.5: sono quasi la stessa scommessa al contrario')
