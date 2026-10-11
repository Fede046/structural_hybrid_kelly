import numpy as np
rng=np.random.default_rng(32)

# --- ambiente: stagione con rottura strutturale a meta ---
T=150; K=4; o=np.array([2.10,3.40,3.80,2.60]); b=o-1
M=40000
def season(seed, sigma_pre=0.015, sigma_post=0.045, ev_pre=0.02, ev_post=-0.05, brk=75):
    rg=np.random.default_rng(seed)
    sig=np.where(np.arange(T)<brk, sigma_pre, sigma_post)
    ev =np.where(np.arange(T)<brk, ev_pre,  ev_post)
    return sig,ev,rg

def agent(mode, seed, lam0=0.25, kappa=0.4, M=M):
    sig,ev,rg=season(seed)
    B=np.ones(M); alive=np.ones(M,bool); mn=np.ones(M)
    resid=np.zeros((M,20)); ptr=0
    for t in range(T):
        p_true=(1+ev[t])/o[0]; EVt=ev[t]
        # edge STIMATO rumoroso
        noise=rg.normal(0,sig[t],M)
        EVhat=np.clip(EVt+noise*o[0],-0.2,0.5)
        fstar=np.clip(EVhat/b[0],0,None)
        # --- supervisore ---
        if mode=='C0':                       # nessun supervisore
            lam=lam0
        elif mode=='C1':                      # rileva ma non gradua: riduzione fissa all'allarme
            sd=resid[:,:min(t,20)].std(1) if t>3 else np.zeros(M)
            alarm=sd>0.030
            lam=np.where(alarm,lam0*kappa,lam0)
        elif mode=='C2':                      # rileva E gradua: lambda* = 1/(1+Var(c))
            sd=resid[:,:min(t,20)].std(1) if t>3 else np.full(M,sig[0])
            sd=np.maximum(sd,0.005)
            EVp=np.maximum(np.abs(EVhat),0.005)
            lam=1/(1+(o[0]*sd/EVp)**2)
            lam=np.minimum(lam,1.0)
        f=np.clip(fstar*lam,0,0.25)
        win=rg.random(M)<p_true
        r=np.where(win,f*b[0],-f)
        B=np.where(alive,B*(1+r),B); mn=np.minimum(mn,B)
        # residuo osservato (proxy dell errore del modello)
        resid[:,ptr%20]=np.where(win,1,0)-p_true-noise*0; ptr+=1
        resid[:,ptr%20]=noise
    dd=1-mn/1.0
    return B, dd, np.mean(B<0.5)

print('=== ABLAZIONE INTERNA DELL AGENTE C ===')
print(' stagione con rottura a meta: sigma 0.015->0.045, EV vero +2% -> -5%')
print(f'{"braccio":40s}{"crescita mediana":>19s}{"q05":>9s}{"max DD medio":>14s}{"P(B<0.5)":>11s}')
res={}
for mode,lbl in [('C0','C0  supervisore SPENTO (lambda fissa)'),
                 ('C1','C1  rileva ma NON gradua (kappa=0.4)'),
                 ('C2','C2  rileva E gradua (lambda*)')]:
    B,dd,ruin=agent(mode,7)
    res[mode]=(np.median(B),np.quantile(B,0.05),dd.mean(),ruin)
    print(f'{lbl:40s}{np.median(B):19.4f}{np.quantile(B,0.05):9.4f}{dd.mean():14.4f}{ruin*100:10.3f}%')
print()
tot=res['C2'][0]-res['C0'][0]; det=res['C1'][0]-res['C0'][0]; gra=res['C2'][0]-res['C1'][0]
print(f' effetto TOTALE del supervisore (C2-C0) sulla mediana: {tot:+.4f}')
print(f'   di cui attribuibile al RILEVARE  (C1-C0): {det:+.4f}  ({det/tot*100 if tot else 0:.0f}%)')
print(f'   di cui attribuibile al GRADUARE  (C2-C1): {gra:+.4f}  ({gra/tot*100 if tot else 0:.0f}%)')
print()
print(' stesso conto sul drawdown medio:')
tot=res['C0'][2]-res['C2'][2]; det=res['C0'][2]-res['C1'][2]; gra=res['C1'][2]-res['C2'][2]
print(f'   riduzione totale {tot:+.4f}  |  rilevare {det:+.4f} ({det/tot*100 if tot else 0:.0f}%)  |  graduare {gra:+.4f} ({gra/tot*100 if tot else 0:.0f}%)')
