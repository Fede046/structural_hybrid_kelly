import numpy as np
from scipy.stats import poisson
rng=np.random.default_rng(7)
N=300_000
lam_h=np.exp(rng.normal(np.log(1.53),0.33,N)); lam_a=np.exp(rng.normal(np.log(1.18),0.33,N))
K=np.arange(15); A=poisson.pmf(K[:,None],lam_h[None,:]); B=poisson.pmf(K[:,None],lam_a[None,:])
P=np.einsum('in,jn->nij',A,B); iu=np.triu_indices(15,1); il=np.tril_indices(15,-1)
p_true=np.stack([P[:,il[0],il[1]].sum(1),np.einsum('nii->n',P),P[:,iu[0],iu[1]].sum(1)],1)
p_true/=p_true.sum(1,keepdims=True)
idx=np.arange(N)

# MERCATO: efficiente ovunque tranne una nicchia (10% delle partite) dove sbaglia
niche=np.zeros(N,bool); niche[:N//10]=True
q=p_true.copy()
shift=np.zeros_like(q); shift[niche,0]=-0.06; shift[niche,2]=+0.06   # mercato sottovaluta la casa nella nicchia
q=np.clip(q+shift,1e-3,None); q/=q.sum(1,keepdims=True)
OM=0.053; pt=q*(1+OM); o=1/pt
y=(rng.random(N)[:,None]>p_true.cumsum(1)).sum(1)

# MODELLO: esatto nella nicchia, rumoroso altrove
phat=p_true.copy()
noise=rng.normal(0,0.055,(N,3)); phat[~niche]=np.clip(p_true[~niche]+noise[~niche],1e-3,None)
phat/=phat.sum(1,keepdims=True)

g=np.mean(np.log(phat[idx,y])-np.log(q[idx,y]))
print(f'g_hat aggregato = {g:+.6f}   ({"NEGATIVO" if g<0 else "positivo"})')
print(f'  g_hat nella nicchia  = {np.mean(np.log(phat[niche][np.arange(niche.sum()),y[niche]])-np.log(q[niche][np.arange(niche.sum()),y[niche]])):+.6f}')
m=~niche
print(f'  g_hat fuori nicchia  = {np.mean(np.log(phat[m][np.arange(m.sum()),y[m]])-np.log(q[m][np.arange(m.sum()),y[m]])):+.6f}')

EVtrue=p_true*o-1; EVhat=phat*o-1
sel=EVhat>0.02
print(f'\nscommesse selezionate (EV_hat>2%): {sel.sum():,}')
print(f'  EV VERO medio su tutte le selezionate      = {EVtrue[sel].mean():+.5f}')
sn=sel&niche[:,None]; so=sel&(~niche)[:,None]
print(f'  di cui NELLA nicchia: {sn.sum():,}  EV vero medio = {EVtrue[sn].mean():+.5f}')
print(f'  di cui FUORI nicchia: {so.sum():,}  EV vero medio = {EVtrue[so].mean():+.5f}')
print('\n=> g_hat aggregato NEGATIVO ma esistono scommesse a EV vero POSITIVO.')
print('   Il filtro sbagliato e scommettere ovunque; il rimedio e selezionare il regime.')

# crescita Kelly ottima (con cassa) sul vero p, vs crescita usando phat
def kelly_growth(pp, o_, p_real, yy, lam=1.0):
    f=np.clip((pp*o_-1)/(o_-1),0,None)
    f=np.minimum(f,0.2)*lam
    # una scommessa per riga: prendi l'esito con f massimo
    j=f.argmax(1); fj=f[np.arange(len(f)),j]
    win=(yy==j)
    r=np.where(win, fj*(o_[np.arange(len(f)),j]-1), -fj)
    return np.mean(np.log1p(r))
print(f'\ncrescita log/partita puntando secondo phat (quarto-Kelly): {kelly_growth(phat,o,p_true,y,0.25):+.6e}')
print(f'crescita log/partita puntando SOLO nella nicchia (quarto-Kelly): ',end='')
fn=kelly_growth(phat[niche],o[niche],p_true[niche],y[niche],0.25)
print(f'{fn*niche.mean():+.6e}  (per partita del campione totale)')
