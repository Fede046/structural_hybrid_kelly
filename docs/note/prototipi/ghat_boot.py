import numpy as np
rng=np.random.default_rng(55)

# d_t autocorrelato: la qualita del modello deriva lentamente nella stagione
def make_series(T, phi, sd_d, g):
    e=rng.normal(0,1,T); x=np.zeros(T)
    for t in range(1,T): x[t]=phi*x[t-1]+e[t]
    x=x/ x.std() * sd_d
    return g + x

def iid_boot_se(d,B=2000):
    n=len(d); return np.array([d[rng.integers(0,n,n)].mean() for _ in range(B)]).std()
def block_boot_se(d,L,B=2000):
    n=len(d); k=int(np.ceil(n/L)); starts=n-L+1
    out=[]
    for _ in range(B):
        s=rng.integers(0,starts,k)
        out.append(np.concatenate([d[i:i+L] for i in s])[:n].mean())
    return np.array(out).std()

T=380; sd_d=0.058; g=0.003
print('=== SE di g_hat: iid vs block bootstrap, serie autocorrelata (T=380) ===')
print(f'{"phi":>6s}{"SE vera (MC)":>14s}{"SE iid boot":>13s}{"SE block L=19":>15s}{"SE block L=38":>15s}{"sottostima iid":>16s}')
for phi in [0.0,0.2,0.4,0.6,0.8]:
    mc=np.array([make_series(T,phi,sd_d,g).mean() for _ in range(4000)]).std()
    d=make_series(T,phi,sd_d,g)
    si=iid_boot_se(d); b19=block_boot_se(d,19); b38=block_boot_se(d,38)
    print(f'{phi:6.1f}{mc:14.6f}{si:13.6f}{b19:15.6f}{b38:15.6f}{mc/si:15.2f}x')

print('\n=== costo del vincolo "almeno una scommessa per giornata" (puntata minima 1 penny) ===')
B0=100_000.0; floor=0.01; EV=-0.05
print(f' frazione del bankroll a puntata minima con B=100k: {floor/B0:.2e}')
print(f' drag atteso su 38 giornate: {38*(floor/B0)*abs(EV):.3e} (log-crescita) -> trascurabile')
for B in [100_000,10_000,1_000,100,10,1,0.2]:
    print(f'   bankroll {B:>9,.2f} -> puntata minima = {floor/B*100:8.4f}% del bankroll')
print(' -> il floor diventa rilevante solo sotto ~20 GBP: e conseguenza della rovina, non causa')
