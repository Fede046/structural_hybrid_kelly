import numpy as np
from scipy.optimize import brentq
from scipy.stats import poisson

def devig(pt, method):
    S = pt.sum(); Om = S-1; n = len(pt)
    if method=='prop': return pt/S
    if method=='add':  return pt - Om/n
    if method=='pow':  return pt**brentq(lambda k: np.sum(pt**k)-1, 0.2, 20)
    if method=='shin':
        f=lambda z: np.sum((np.sqrt(z**2+4*(1-z)*pt**2/S)-z)/(2*(1-z)))-1
        try: z=brentq(f,1e-12,0.45)
        except ValueError: z=1e-12
        return (np.sqrt(z**2+4*(1-z)*pt**2/S)-z)/(2*(1-z))
    if method=='or':
        OR=brentq(lambda OR:(pt/(OR+pt-OR*pt)).sum()-1,1e-8,1e4); return pt/(OR+pt-OR*pt)
    if method=='wpo':
        o=1/pt; n=len(pt); M=Om; return (n-M*o)/(n*o)

# DGP realistico stile Premier League: Poisson bivariata indipendente
rng = np.random.default_rng(20260914)
N = 20000
# forze attacco/difesa realistiche -> gol attesi
lam_h = np.exp(rng.normal(np.log(1.53), 0.33, N))   # media gol casa ~1.53
lam_a = np.exp(rng.normal(np.log(1.18), 0.33, N))   # media gol trasferta ~1.18
K = np.arange(0, 15)
ph = poisson.pmf(K[:,None], lam_h[None,:])   # 15 x N
pa = poisson.pmf(K[:,None], lam_a[None,:])
P = np.einsum('in,jn->nij', ph, pa)
iu = np.triu_indices(15,1); il = np.tril_indices(15,-1)
p_home = P[:, il[0], il[1]].sum(axis=1)
p_away = P[:, iu[0], iu[1]].sum(axis=1)
p_draw = np.einsum('nii->n', P)
p_true = np.stack([p_home, p_draw, p_away], axis=1)
p_true = p_true/p_true.sum(axis=1, keepdims=True)

print('DGP: distribuzione di p_true (quantili)')
for j,l in enumerate(['casa','pari','trasf']):
    q=np.quantile(p_true[:,j],[0.01,0.05,0.5,0.95,0.99])
    print(f'  {l:6s} 1% {q[0]:.3f}  5% {q[1]:.3f}  mediana {q[2]:.3f}  95% {q[3]:.3f}  99% {q[4]:.3f}')
print(f'  quota outsider massima implicita: {1/p_true.min():.1f}')
print(f'  frequenza pareggi: {p_true[:,1].mean():.3f}  vittorie casa: {p_true[:,0].mean():.3f}')

OM=0.053; a,g = 0.008, 0.40
make = lambda p,c: p*(1+a+c*(1.0/p-1.0)**g)
c = brentq(lambda c: np.mean(make(p_true,c).sum(axis=1))-1-OM, 1e-10, 5.0)
pt = make(p_true,c)
Om = pt.sum(axis=1)-1
print(f'\nBookmaker con FL bias: Omega medio {Om.mean()*100:.3f}%, range [{Om.min()*100:.2f}, {Om.max()*100:.2f}]%')
print(f'  vig relativo sul favorito medio: {np.mean(1-p_true[:,0]/pt[:,0])*100:.2f}%')
print(f'  vig relativo sull outsider medio: {np.mean(1-p_true.min(axis=1)/pt[np.arange(N),p_true.argmin(axis=1)])*100:.2f}%')

u=rng.random(N); y=(u[:,None]>p_true.cumsum(axis=1)).sum(axis=1)
print('\n--- confronto sui dati simulati (N=20000) ---')
res={}
for m in ['prop','add','pow','shin','or','wpo']:
    Q=np.array([devig(pt[i],m) for i in range(N)])
    q=np.clip(Q,1e-12,1)
    ll=-np.mean(np.log(q[np.arange(N),y])); res[m]=ll
    rmse=np.sqrt(np.mean((Q-p_true)**2))
    print(f'  {m:5s} log-loss {ll:.6f}  RMSE {rmse:.6f}  bias outsider {np.mean(Q.min(axis=1)-p_true.min(axis=1))*100:+.3f}pp  q<=0: {(Q<=0).sum()}')
ll_t=-np.mean(np.log(p_true[np.arange(N),y]))
print(f'  {"VERA":5s} log-loss {ll_t:.6f}')
sp=max(res.values())-min(res.values())
print(f'\n  spread log-loss tra metodi = {sp:.6f}')
print(f'  confronto: g_hat di GPT-5.4 in KellyBench = 0.974-0.971 = 0.003')
print(f'  --> il de-vigging vale il {sp/0.003*100:.1f}% di quel segnale')
