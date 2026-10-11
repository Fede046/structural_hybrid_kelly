import numpy as np
rng=np.random.default_rng(2027)

# ---------- OB decomposition su loss del modello ----------
def ob_decompose(X0,L0,X1,L1):
    """Oaxaca-Blinder: differenza media di L fra periodo1 e periodo0,
       scomposta in composizione (cambia X) e struttura (cambiano i coefficienti)."""
    A0=np.c_[np.ones(len(X0)),X0]; A1=np.c_[np.ones(len(X1)),X1]
    b0=np.linalg.lstsq(A0,L0,rcond=None)[0]; b1=np.linalg.lstsq(A1,L1,rcond=None)[0]
    m0=A0.mean(0); m1=A1.mean(0)
    tot=L1.mean()-L0.mean()
    comp=(m1-m0)@b0          # composizione, valutata ai coefficienti del periodo 0
    stru=m1@(b1-b0)          # struttura
    return tot,comp,stru

N=40000
print('=== A. mappatura virtual/real -> compositivo/strutturale, con TUTTE le covariate osservate ===')
print(f'{"scenario":34s}{"totale":>10s}{"composiz.":>11s}{"struttur.":>11s}{"verdetto":>14s}')
# X: due covariate osservabili (es. differenziale Elo, fascia di quota)
def gen(n, muX, beta, sd=0.30):
    X=rng.normal(muX,1.0,(n,2))
    L=beta[0]+X@beta[1:]+rng.normal(0,sd,n)   # L = loss del modello
    return X,L
beta0=np.array([1.00,0.30,-0.20])
X0,L0=gen(N,[0.0,0.0],beta0)
# 1) VIRTUAL puro: cambia P(X), stessa relazione
X1,L1=gen(N,[0.6,0.0],beta0)
t,c,s=ob_decompose(X0,L0,X1,L1); print(f'{"virtual puro (cambia P(X))":34s}{t:10.4f}{c:11.4f}{s:11.4f}{"compositivo":>14s}')
# 2) REAL puro: stessa P(X), cambiano i coefficienti
X1,L1=gen(N,[0.0,0.0],np.array([1.25,0.30,-0.20]))
t,c,s=ob_decompose(X0,L0,X1,L1); print(f'{"real puro (cambia P(y|X))":34s}{t:10.4f}{c:11.4f}{s:11.4f}{"strutturale":>14s}')
# 3) misto
X1,L1=gen(N,[0.6,0.0],np.array([1.25,0.30,-0.20]))
t,c,s=ob_decompose(X0,L0,X1,L1); print(f'{"misto":34s}{t:10.4f}{c:11.4f}{s:11.4f}{"entrambi":>14s}')

print('\n=== B. IL PROBLEMA: covariata NON osservata ===')
print('   DGP: virtual drift PURO su una terza covariata Z che l analista non osserva')
def gen3(n,muX,muZ,beta,sd=0.30):
    X=rng.normal(muX,1.0,(n,2)); Z=rng.normal(muZ,1.0,n)
    L=beta[0]+X@beta[1:3]+beta[3]*Z+rng.normal(0,sd,n)
    return X,Z,L
b=np.array([1.00,0.30,-0.20,0.45])
X0,Z0,L0=gen3(N,[0,0],0.0,b)
print(f'{"shift su Z":>12s}{"totale":>10s}{"composiz.":>11s}{"struttur.":>11s}{"% attribuita a STRUTTURA":>26s}')
for dz in [0.0,0.3,0.6,1.0]:
    X1,Z1,L1=gen3(N,[0,0],dz,b)     # SOLO P(Z) cambia: e virtual drift puro
    t,c,s=ob_decompose(X0,L0,X1,L1)
    pct = s/t*100 if abs(t)>1e-9 else 0
    print(f'{dz:12.1f}{t:10.4f}{c:11.4f}{s:11.4f}{pct:25.1f}%')
print('   -> drift VIRTUALE puro attribuito quasi INTERAMENTE alla componente STRUTTURALE')
print('      perche la covariata che si muove non e nel modello.')
print('   controllo: includendo Z fra le covariate osservate ->', end=' ')
def ob3(X0,Z0,L0,X1,Z1,L1):
    A0=np.c_[np.ones(len(X0)),X0,Z0]; A1=np.c_[np.ones(len(X1)),X1,Z1]
    b0=np.linalg.lstsq(A0,L0,rcond=None)[0]; b1=np.linalg.lstsq(A1,L1,rcond=None)[0]
    return L1.mean()-L0.mean(), (A1.mean(0)-A0.mean(0))@b0, A1.mean(0)@(b1-b0)
X1,Z1,L1=gen3(N,[0,0],1.0,b)
t,c,s=ob3(X0,Z0,L0,X1,Z1,L1); print(f'tot {t:.4f}  comp {c:.4f}  stru {s:.4f}  -> compositivo, corretto')
