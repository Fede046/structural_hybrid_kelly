import numpy as np
T=150; o=2.10; b=o-1; M=30000
def run(mode,kappa=0.4,lam0=0.25,seed=7):
    rg=np.random.default_rng(seed)
    sig=np.where(np.arange(T)<75,0.015,0.045); ev=np.where(np.arange(T)<75,0.02,-0.05)
    B=np.ones(M); mn=np.ones(M); resid=np.zeros((M,20))
    for t in range(T):
        p=(1+ev[t])/o
        noise=rg.normal(0,sig[t],M)
        EVhat=np.clip(ev[t]+noise*o,-0.2,0.5); fstar=np.clip(EVhat/b,0,None)
        sd=resid[:,:min(t,20)].std(1) if t>3 else np.full(M,sig[0])
        if mode=='C0': lam=np.full(M,lam0)
        elif mode=='C1': lam=np.where(sd>0.030,lam0*kappa,lam0)
        else:
            sdc=np.maximum(sd,0.005); EVp=np.maximum(np.abs(EVhat),0.005)
            lam=np.minimum(1/(1+(o*sdc/EVp)**2),1.0)
        f=np.clip(fstar*lam,0,0.25)
        win=rg.random(M)<p
        B=B*(1+np.where(win,f*b,-f)); mn=np.minimum(mn,B)
        resid[:,t%20]=noise
    return np.median(B),(1-mn).mean()

print('=== C1 ha un iperparametro libero, C2 no. Quanto conta? ===')
print(f'{"kappa di C1":>12s}{"crescita mediana":>19s}{"max DD medio":>15s}')
best=None
for k in [0.1,0.2,0.4,0.6,0.8,1.0]:
    g,d=run('C1',kappa=k)
    print(f'{k:12.2f}{g:19.4f}{d:15.4f}')
g0,d0=run('C0'); g2,d2=run('C2')
print(f'{"C0 (nessuno)":>12s}{g0:19.4f}{d0:15.4f}')
print(f'{"C2 (lambda*)":>12s}{g2:19.4f}{d2:15.4f}   <- nessun iperparametro da tarare')
print()
print(' -> C1 spazia da',f'{min(run("C1",kappa=k)[0] for k in [0.1,0.4,1.0]):.4f}','a',f'{max(run("C1",kappa=k)[0] for k in [0.1,0.4,1.0]):.4f}','a seconda di kappa')
print('    C2 e un punto solo: la graduazione non aggiunge gradi di liberta al ricercatore')

print('\n=== perche il supervisore NON deve toccare le previsioni ===')
rg=np.random.default_rng(11)
N=60000
q=np.clip(rg.beta(4,5,N),0.05,0.9); om=1.053; ob=1/(q*om)
ph=np.clip(q+rg.normal(0,0.025,N),0.01,0.99)
def sel(p,delta=0.0): return (p*ob-1)>delta
A=sel(ph)                                  # supervisore tocca solo lambda
w=0.7; lo=lambda x: np.log(x/(1-x)); inv=lambda z:1/(1+np.exp(-z))
ph2=inv(w*lo(ph)+(1-w)*lo(q))              # supervisore "corregge" anche p_hat
Bsel=sel(ph2)
J=(A&Bsel).sum()/(A|Bsel).sum()
print(f' scommesse selezionate: solo-lambda {A.sum():,}   con shrinkage su p_hat {Bsel.sum():,}')
print(f' indice di Jaccard fra i due insiemi: {J*100:.1f}%')
print(f' scommesse presenti in uno e non nell altro: {(A^Bsel).sum():,} ({(A^Bsel).sum()/(A|Bsel).sum()*100:.1f}% dell unione)')
print(' -> il confronto appaiato si rompe: gli agenti non scommettono piu sulle stesse partite,')
print('    e la differenza di risultato non e piu attribuibile alla sola regola di staking.')
