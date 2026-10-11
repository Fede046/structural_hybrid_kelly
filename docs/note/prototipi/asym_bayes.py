import numpy as np
from scipy.optimize import brentq

def G(f,p,o):
    b=o-1
    f=np.clip(f,0,0.999)
    return p*np.log(1+b*f)+(1-p)*np.log(1-f)

print('=== asimmetria sovra/sotto-stima: perdita di crescita ===')
print('  eps = errore RELATIVO su p.  Perdita = G(f*) - G(f_hat)')
print(f'{"o":>5s}{"p":>7s}{"EV":>8s}{"eps":>6s}{"perdita SOPRA":>15s}{"perdita SOTTO":>15s}{"rapporto":>11s}{"trunc?":>8s}')
for o,EV in [(2.5,0.05),(2.5,0.15),(1.5,0.10),(6.5,0.05)]:
    p=(1+EV)/o; b=o-1; fs=EV/b
    for eps in [0.10,0.20]:
        fu=( (1+eps)*p*o-1)/b
        fd=( (1-eps)*p*o-1)/b
        fd_t=max(fd,0.0)
        L_up=G(fs,p,o)-G(fu,p,o)
        L_dn_raw=G(fs,p,o)-G(fd,p,o) if fd>-0.999 else np.nan
        L_dn=G(fs,p,o)-G(fd_t,p,o)
        print(f'{o:5.1f}{p:7.3f}{EV:8.3f}{eps:6.2f}{L_up:15.3e}{L_dn:15.3e}{L_dn/L_up:11.3f}{"SI" if fd<0 else "no":>8s}')

print('\n=== senza troncamento (f_hat negativo ammesso: puntata sul complementare) ===')
for o,EV,eps in [(2.5,0.30,0.10),(1.5,0.40,0.10),(2.5,0.50,0.10)]:
    p=(1+EV)/o; b=o-1; fs=EV/b
    fu=((1+eps)*p*o-1)/b; fd=((1-eps)*p*o-1)/b
    L_up=G(fs,p,o)-G(fu,p,o); L_dn=G(fs,p,o)-G(fd,p,o)
    print(f' o={o} p={p:.3f} EV={EV} fd={fd:+.4f}>0 -> perdita sopra {L_up:.3e}  sotto {L_dn:.3e}  rapporto sotto/sopra {L_dn/L_up:.4f}')

print('\n=== Kelly bayesiano: E_posterior[G(f,p)] e lineare in p ===')
rng=np.random.default_rng(3)
o=2.5; b=o-1
post=rng.beta(42,58,200_000)   # posteriore su p, media 0.42
print(f' media posteriore E[p] = {post.mean():.6f}, sd = {post.std():.6f}')
grid=np.linspace(0.0,0.6,6001)
obj=[np.mean(post*np.log(1+b*f)+(1-post)*np.log(1-f)) for f in grid]
f_bayes=grid[int(np.argmax(obj))]
f_plug=(post.mean()*o-1)/b
print(f' argmax numerico su posteriore = {f_bayes:.5f}')
print(f' Kelly plug-in con la MEDIA posteriore = {f_plug:.5f}')
print(f' differenza = {abs(f_bayes-f_plug):.2e}   -> coincidono')

print('\n=== Kelly robusto (minimax su intervallo di credibilita) ===')
lo,hi=np.quantile(post,[0.05,0.95])
print(f' intervallo 90%: [{lo:.4f}, {hi:.4f}]')
f_rob=(lo*o-1)/b
print(f' Kelly sul caso peggiore p={lo:.4f} -> f={max(f_rob,0):.5f}  (vs plug-in {f_plug:.5f})')
print(f' rapporto f_robusto/f_plug = {max(f_rob,0)/f_plug:.4f}')
