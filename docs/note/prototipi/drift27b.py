import numpy as np
rng=np.random.default_rng(77)

print('=== C. doppio drift: l edge dipende dalla DIFFERENZA di velocita ===')
T=60
theta=np.r_[np.zeros(10), np.ones(T-10)]      # shock strutturale a t=10
def adapt(x, alpha):                           # adattamento esponenziale con tasso alpha
    y=np.zeros_like(x)
    for t in range(1,len(x)): y[t]=y[t-1]+alpha*(x[t]-y[t-1])
    return y
print(f'{"alpha_mercato":>14s}{"alpha_modello":>14s}{"errore cum. mkt":>17s}{"errore cum. mod":>17s}{"g_hat proxy":>14s}')
for am,ad in [(0.60,0.60),(0.60,0.15),(0.15,0.60),(0.90,0.10),(0.30,0.30)]:
    qm=adapt(theta,am); pm=adapt(theta,ad)
    em=np.sum((theta-qm)**2); ed=np.sum((theta-pm)**2)
    print(f'{am:14.2f}{ad:14.2f}{em:17.3f}{ed:17.3f}{em-ed:+14.3f}')
print('  g_hat proxy = errore del mercato - errore del modello (positivo = il modello vince)')
print('  -> stessa dimensione di shock: il segno dipende SOLO da chi si adatta prima')

print('\n=== D. velocita di riprezzamento: quanto dura la finestra ===')
print(' tempo per recuperare il 90% dello shock: t = ln(0.1)/ln(1-alpha)')
for a in [0.05,0.10,0.15,0.30,0.60,0.90]:
    print(f'   alpha={a:4.2f} -> {np.log(0.1)/np.log(1-a):6.1f} giornate')
print(' un Elo con K tipico ha alpha efficace basso: serve una stagione parziale.')
print(' il mercato incorpora una notizia in ORE.')

print('\n=== E. neopromosse: sensibilita della probabilita alla inizializzazione Elo ===')
def elo_p(d, ha=60, s=400):    # P(casa vince) stile Elo a due esiti
    return 1/(1+10**(-(d+ha)/s))
print(f'{"errore init (Elo pt)":>21s}{"P(1) vera":>11s}{"P(1) stimata":>14s}{"errore pp":>11s}{"errore rel.":>13s}')
d_true=0
for err in [0,50,100,150,200,300]:
    pt=elo_p(d_true); pe=elo_p(d_true+err)
    print(f'{err:21d}{pt:11.4f}{pe:14.4f}{(pe-pt)*100:+11.2f}{(pe-pt)/pt*100:+12.1f}%')
print()
print(' convergenza dell Elo dopo n partite con fattore K (errore residuo = err*(1-K/ (K+...)) ~ decadimento):')
for K in [20,30,40]:
    for n in [5,10,19,38]:
        # approssimazione: ogni partita corregge in media K*|p_obs-p_exp|, decadimento ~ (1-K/400*ln10*p(1-p)*400)... 
        pass
# simulazione onesta della convergenza
def sim_conv(K, err0, n, reps=4000):
    res=[]
    for _ in range(reps):
        r=err0
        for _ in range(n):
            p_exp=elo_p(r); p_true=elo_p(0)
            out=rng.random()<p_true
            r += K*((1 if out else 0)-p_exp)*(-1)   # rating relativo: correzione verso il vero
        res.append(r)
    return np.mean(res), np.std(res)
print(f'{"K":>4s}{"n partite":>11s}{"errore residuo medio":>22s}{"sd":>8s}')
for K in [20,40]:
    for n in [5,10,19,38]:
        m,s=sim_conv(K,150,n)
        print(f'{K:4d}{n:11d}{m:22.1f}{s:8.1f}')
