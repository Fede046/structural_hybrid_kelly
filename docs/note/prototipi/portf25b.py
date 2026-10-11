import numpy as np, itertools
from scipy.optimize import minimize
rng=np.random.default_rng(9)

print('=== 6b. dove il "Kelly separato" si rompe: due esiti dello STESSO match ===')
p=np.array([0.45,0.27,0.28]); o=np.array([2.30,3.60,3.60])
f_sep=np.clip((p*o-1)/(o-1),0,None)
P=p; R=np.eye(3)*(o-1)+ (np.ones((3,3))-np.eye(3))*(-1.0)   # riga = esito realizzato
def negG(f):
    w=1+R@f
    if np.any(w<=1e-9): return 1e6
    return -np.sum(P*np.log(w))
r=minimize(negG,f_sep*0.3,bounds=[(0,0.9)]*3,constraints={'type':'ineq','fun':lambda f:0.999-f.sum()},method='SLSQP')
print(' p =',p,' o =',o)
print(' Kelly separato :',np.round(f_sep,4),' somma',round(f_sep.sum(),4),' crescita',round(-negG(f_sep),6))
print(' Kelly esatto   :',np.round(r.x,4),' somma',round(r.x.sum(),4),' crescita',round(-negG(r.x),6))
print(f' guadagno del trattamento congiunto: {(-negG(r.x))-(-negG(f_sep)):+.6f}  ({((-negG(r.x))/(-negG(f_sep))-1)*100:+.1f}%)')

print('\n=== 7b. il bias che conta e quello PERSISTENTE fra giornate, non quello interno alla giornata ===')
D=6000; K=6
p=np.array([0.52,0.40,0.35,0.60,0.30,0.45]); o=np.array([2.10,2.80,3.20,1.85,3.80,2.40])
def run(phi, sd_tot=0.028, M=4000):
    out=[]
    for _ in range(M//200):
        # bias comune AR(1) nel tempo
        sd_c=sd_tot*0.7; sd_i=np.sqrt(sd_tot**2-sd_c**2)
        e=rng.normal(0,sd_c*np.sqrt(1-phi**2),(200,D//200 if False else 60))
        b=np.zeros_like(e)
        for t in range(1,e.shape[1]): b[:,t]=phi*b[:,t-1]+e[:,t]
        idio=rng.normal(0,sd_i,(200,b.shape[1],K))
        ph=np.clip(p+b[:,:,None]+idio,0.02,0.95)
        f=np.clip((ph*o-1)/(o-1),0,None)*0.25
        W=rng.random((200,b.shape[1],K))<p
        R2=np.where(W,(o-1),-1.0)
        daily=(f*R2).sum(2)
        out.append(np.log1p(np.clip(daily,-0.95,None)).sum(1))
    return np.concatenate(out)
print(f'{"phi (persistenza bias)":>24s}{"sd log-ricchezza 60gg":>24s}{"rapporto vs phi=0":>20s}')
base=None
for phi in [0.0,0.3,0.6,0.9]:
    x=run(phi); s=x.std()
    if base is None: base=s
    print(f'{phi:24.1f}{s:24.5f}{s/base:20.3f}')
print(' -> un bias comune che PERSISTE fra giornate gonfia la varianza del bankroll;')
print('    un bias comune fresco ogni giornata no, perche gli esiti sono indipendenti')
