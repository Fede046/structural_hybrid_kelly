import numpy as np, io, contextlib
from scipy.stats import poisson, norm
rng=np.random.default_rng(101)
N=400_000
lam_h=np.exp(rng.normal(np.log(1.53),0.33,N)); lam_a=np.exp(rng.normal(np.log(1.18),0.33,N))
K=np.arange(15); A=poisson.pmf(K[:,None],lam_h[None,:]); B=poisson.pmf(K[:,None],lam_a[None,:])
P=np.einsum('in,jn->nij',A,B); iu=np.triu_indices(15,1); il=np.tril_indices(15,-1)
p_true=np.stack([P[:,il[0],il[1]].sum(1),np.einsum('nii->n',P),P[:,iu[0],iu[1]].sum(1)],1)
p_true/=p_true.sum(1,keepdims=True); idx=np.arange(N)
q=p_true.copy(); y=(rng.random(N)[:,None]>p_true.cumsum(1)).sum(1)

print('=== potenza di g_hat: sd del termine per partita ===')
print(f'{"sd rumore modello":>18s}{"E[g_hat]":>12s}{"sd(d_t)":>11s}{"SE 380 match":>14s}{"SE 1900":>10s}{"n per |g|=0.003":>17s}')
for s in [0.0,0.005,0.010,0.020,0.030]:
    ph=np.clip(p_true+rng.normal(0,s,(N,3)),1e-4,None); ph/=ph.sum(1,keepdims=True)
    d=np.log(ph[idx,y])-np.log(q[idx,y])
    g=d.mean(); sd=d.std()
    n_need=(1.96*sd/0.003)**2
    print(f'{s:18.3f}{g:12.6f}{sd:11.5f}{sd/np.sqrt(380):14.6f}{sd/np.sqrt(1900):10.6f}{n_need:17,.0f}')
print('\n  -> 380 partite = 1 stagione;  1900 = 5 stagioni')

print('\n=== quale g_hat e rilevabile in una stagione (380 partite)? ===')
for s in [0.005,0.010,0.020]:
    ph=np.clip(p_true+rng.normal(0,s,(N,3)),1e-4,None); ph/=ph.sum(1,keepdims=True)
    d=np.log(ph[idx,y])-np.log(q[idx,y]); sd=d.std()
    print(f'  sd rumore={s}: |g_hat| minimo rilevabile a 95% su 380 match = {1.96*sd/np.sqrt(380):.5f}')

print('\n=== distorsione IN-SAMPLE di g_hat (modello calibrato sugli stessi dati) ===')
# modello = frequenze empiriche stimate su n partite "simili" -> analogia: stima su piccolo campione
for n_train in [50,200,1000]:
    gs=[]
    for _ in range(400):
        i=rng.integers(0,N,n_train)
        # modello: media delle p_true del blocco + shrink verso le frequenze osservate (overfit)
        yy=y[i]; freq=np.bincount(yy,minlength=3)/n_train
        ph=np.clip(0.5*p_true[i]+0.5*freq,1e-4,None); ph/=ph.sum(1,keepdims=True)
        d_in=np.log(ph[np.arange(n_train),yy])-np.log(q[i][np.arange(n_train),yy])
        j=rng.integers(0,N,n_train)     # campione fresco, stesso modello (freq del train)
        ph2=np.clip(0.5*p_true[j]+0.5*freq,1e-4,None); ph2/=ph2.sum(1,keepdims=True)
        d_out=np.log(ph2[np.arange(n_train),y[j]])-np.log(q[j][np.arange(n_train),y[j]])
        gs.append((d_in.mean(),d_out.mean()))
    gs=np.array(gs)
    print(f'  n_train={n_train:5d}:  g_hat in-sample={gs[:,0].mean():+.6f}   out-of-sample={gs[:,1].mean():+.6f}   distorsione={gs[:,0].mean()-gs[:,1].mean():+.6f}')
