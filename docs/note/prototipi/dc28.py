import numpy as np
from scipy.stats import poisson
np.set_printoptions(precision=6,suppress=True)

print('=== 1. Elo == Bradley-Terry con pi_i = 10^(R_i/400) ===')
R=np.array([1600.0,1450.0])
p_elo=1/(1+10**(-(R[0]-R[1])/400))
pi=10**(R/400); p_bt=pi[0]/pi.sum()
print(f' Elo {p_elo:.10f}   Bradley-Terry {p_bt:.10f}   diff {abs(p_elo-p_bt):.2e}')
print(' -> identiche: Elo E UNA parametrizzazione di Bradley-Terry')
# l update Elo e un passo di gradiente sulla log-verosimiglianza BT
eps=1e-6
def ll(r,S): 
    p=1/(1+10**(-(r-R[1])/400)); return S*np.log(p)+(1-S)*np.log(1-p)
for S in [1.0,0.0]:
    g=(ll(R[0]+eps,S)-ll(R[0]-eps,S))/(2*eps)
    p=1/(1+10**(-(R[0]-R[1])/400))
    print(f' S={S}: d(logL)/dR numerico {g:+.8f}   (S-E)*ln10/400 = {(S-p)*np.log(10)/400:+.8f}')
print(' -> update Elo R += K(S-E) e gradiente ascendente con passo K*400/ln(10) =', round(400/np.log(10),2),'* K')

print('\n=== 2. Dixon-Coles: tau conserva la massa delle quattro celle ===')
def tau(x,y,lam,mu,rho):
    if x==0 and y==0: return 1-lam*mu*rho
    if x==0 and y==1: return 1+lam*rho
    if x==1 and y==0: return 1+mu*rho
    if x==1 and y==1: return 1-rho
    return 1.0
for lam,mu,rho in [(1.53,1.18,-0.13),(2.10,0.80,-0.05),(1.00,1.00,0.10)]:
    P=lambda x,y: poisson.pmf(x,lam)*poisson.pmf(y,mu)
    s_ind=sum(P(x,y) for x in (0,1) for y in (0,1))
    s_dc =sum(P(x,y)*tau(x,y,lam,mu,rho) for x in (0,1) for y in (0,1))
    print(f' lam={lam} mu={mu} rho={rho:+.2f}:  massa indip {s_ind:.10f}  massa DC {s_dc:.10f}  diff {abs(s_ind-s_dc):.2e}')
print(' -> identita esatta: tau ridistribuisce fra le 4 celle senza cambiare il totale')
print('    dimostrazione: A[1-lam*mu*rho] + A*mu[1+lam*rho] + A*lam[1+mu*rho] + A*lam*mu[1-rho] = A[1+lam+mu+lam*mu]')

print('\n=== 3. vincoli di ammissibilita su rho ===')
print(' serve tau > 0 in tutte e quattro le celle:')
print('   1-lam*mu*rho>0 -> rho < 1/(lam*mu)')
print('   1+lam*rho>0    -> rho > -1/lam')
print('   1+mu*rho>0     -> rho > -1/mu')
print('   1-rho>0        -> rho < 1')
print(f'{"lam":>7s}{"mu":>7s}{"rho min":>11s}{"rho max":>11s}')
for lam,mu in [(1.53,1.18),(2.5,0.6),(0.9,0.9),(3.0,0.4)]:
    print(f'{lam:7.2f}{mu:7.2f}{max(-1/lam,-1/mu):11.4f}{min(1/(lam*mu),1.0):11.4f}')

print('\n=== 4. quanto sposta tau le probabilita 1X2 ===')
K=15
def probs(lam,mu,rho):
    A=poisson.pmf(np.arange(K),lam); B=poisson.pmf(np.arange(K),mu)
    P=np.outer(A,B).copy()
    for x in (0,1):
        for y in (0,1): P[x,y]*=tau(x,y,lam,mu,rho)
    i,j=np.indices(P.shape)
    return P[i>j].sum(), P[i==j].sum(), P[i<j].sum(), P[(i+j)>2.5].sum()
print(f'{"rho":>8s}{"P(1)":>9s}{"P(X)":>9s}{"P(2)":>9s}{"P(O2.5)":>10s}{"d P(X) pp":>11s}')
base=probs(1.53,1.18,0.0)
for rho in [0.0,-0.05,-0.10,-0.13,-0.18]:
    p=probs(1.53,1.18,rho)
    print(f'{rho:+8.2f}{p[0]:9.4f}{p[1]:9.4f}{p[2]:9.4f}{p[3]:10.4f}{(p[1]-base[1])*100:+11.3f}')
print(' -> rho negativo (il valore empirico di Dixon-Coles) AUMENTA il pareggio')
