import numpy as np, io, contextlib
from scipy.optimize import brentq
buf=io.StringIO()
with contextlib.redirect_stdout(buf):
    exec(open('devig_real.py').read())

rng2 = np.random.default_rng(99)
sigma = 0.025
noise = rng2.normal(0, sigma, p_true.shape)
p_hat = np.clip(p_true + noise, 1e-4, None); p_hat/=p_hat.sum(axis=1,keepdims=True)
o_book = 1/pt
DELTA = 0.02
print(f'--- selezione scommesse con soglia edge  p_hat - q > {DELTA} ---')
print(f'{"metodo":6s} {"n scomm":>8s} {"%outsider":>10s} {"edge medio":>11s} {"quota media":>12s} {"EV vero medio":>14s}')
is_out = np.zeros(p_true.shape, bool); is_out[np.arange(N), pt.argmin(axis=1)] = True
sets={}
for m in ['prop','add','pow','shin','or']:
    Q=np.array([devig(pt[i],m) for i in range(N)])
    edge=p_hat-Q; sel=edge>DELTA; sets[m]=sel; n=sel.sum()
    print(f'{m:6s} {n:8d} {(sel&is_out).sum()/n*100:9.1f}% {edge[sel].mean():11.4f} {o_book[sel].mean():12.2f} {np.mean(p_true[sel]*o_book[sel]-1):+14.4f}')
base=sets['prop']
print('\nsovrapposizione insiemi di scommesse rispetto a proporzionale (indice di Jaccard):')
for m in ['add','pow','shin','or']:
    j=(base&sets[m]).sum()/(base|sets[m]).sum()
    print(f'  prop vs {m:5s}: {j*100:.1f}%   (scommesse in {m} ma non in prop: {(sets[m]&~base).sum()})')
print('\n--- g_hat = media(ln p_hat - ln q) ---')
for m in ['prop','add','pow','shin','or']:
    Q=np.clip(np.array([devig(pt[i],m) for i in range(N)]),1e-12,1)
    gh=np.mean(np.log(p_hat[np.arange(N),y])-np.log(Q[np.arange(N),y]))
    print(f'  {m:6s} g_hat = {gh:+.6f}')
