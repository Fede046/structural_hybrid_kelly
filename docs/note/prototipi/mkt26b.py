import numpy as np
from scipy.stats import poisson
from scipy.optimize import minimize
np.set_printoptions(precision=4,suppress=True)

# --- Kelly congiunto su 5 tipi di scommessa dello stesso match ---
K=12
def scenario_probs(lh,la):
    A=poisson.pmf(np.arange(K),lh); B=poisson.pmf(np.arange(K),la)
    P=np.outer(A,B); i,j=np.indices(P.shape)
    # 6 celle: (esito 1X2) x (over/under)
    cells={}
    for nm,m in [('1',i>j),('X',i==j),('2',i<j)]:
        for nm2,m2 in [('O',(i+j)>2.5),('U',(i+j)<=2.5)]:
            cells[nm+nm2]=P[m&m2].sum()
    return cells
lh,la=1.53,1.18
cells=scenario_probs(lh,la)
keys=list(cells); pc=np.array([cells[k] for k in keys])
print('celle congiunte (1X2 x O/U):', dict(zip(keys,np.round(pc,4))), ' somma',round(pc.sum(),6))

# quote di mercato: verita + vig proporzionale
p1=sum(cells[k] for k in ['1O','1U']); pX=sum(cells[k] for k in ['XO','XU']); p2=sum(cells[k] for k in ['2O','2U'])
pO=sum(cells[k] for k in ['1O','XO','2O']); pU=1-pO
OM=0.053
o=np.array([1/(p1*(1+OM)),1/(pX*(1+OM)),1/(p2*(1+OM)),1/(pO*(1+OM)),1/(pU*(1+OM))])
names=['home','draw','away','over','under']
print('quote di mercato:', dict(zip(names,np.round(o,3))))

# modello: vede un edge reale su draw e over
phat=np.array([p1,pX,p2,pO,pU])*1.0
phat[1]*=1.14; phat[3]*=1.07
ptrue=np.array([p1,pX,p2,pO,pU])
# in questo esperimento il MODELLO ha ragione: la verita e phat -> ricalcolo le celle coerenti? 
# piu semplice: il modello E la verita, e il mercato sbaglia. Costruisco mercato distorto.
o_mkt=np.array([1/(p1*(1+OM)*1.00),1/(pX*(1+OM)*0.88),1/(p2*(1+OM)*1.00),1/(pO*(1+OM)*0.94),1/(pU*(1+OM)*1.06)])
EV=ptrue*o_mkt-1
print('\nEV vero per tipo:', dict(zip(names,np.round(EV,4))))

# payoff matrix: righe = 6 celle, colonne = 5 scommesse
R=np.zeros((6,5))
for r,k in enumerate(keys):
    res,ou=k[0],k[1]
    win=[res=='1',res=='X',res=='2',ou=='O',ou=='U']
    R[r]=np.where(win,o_mkt-1,-1.0)
def negG(f):
    w=1+R@f
    if np.any(w<=1e-9): return 1e6
    return -np.sum(pc*np.log(w))
f_sep=np.clip(EV/(o_mkt-1),0,None)
r=minimize(negG,f_sep*0.4,bounds=[(0,0.6)]*5,constraints={'type':'ineq','fun':lambda f:0.999-f.sum()},method='SLSQP')
print(f'\n Kelly separato per tipo : {np.round(f_sep,4)}  somma {f_sep.sum():.4f}  crescita {-negG(f_sep):.6f}')
print(f' Kelly congiunto 5 tipi  : {np.round(r.x,4)}  somma {r.x.sum():.4f}  crescita {-negG(r.x):.6f}')
print(f' guadagno congiunto: {(-negG(r.x))-(-negG(f_sep)):+.6f}  ({((-negG(r.x))/(-negG(f_sep))-1)*100:+.1f}%)')

print('\n=== 3. Exchange: margine effettivo della commissione ===')
print(' scommessa back a quota equa o=1/p, commissione c sulle vincite nette')
print(' EV = p*(1+(o-1)(1-c)) - 1 = -c(1-p)   -> margine effettivo = c(1-p)')
print(f'{"p":>7s}{"quota":>8s}{"c=2%":>9s}{"c=3%":>9s}{"c=5%":>9s}{"book 5.3% (vig rel.)":>22s}')
for p in [0.75,0.60,0.45,0.30,0.15,0.08]:
    print(f'{p:7.2f}{1/p:8.2f}'+''.join(f'{c*(1-p)*100:8.2f}%' for c in [0.02,0.03,0.05])+f'{0.053/1.053*100:21.2f}%')
print(' -> commissione equivalente a un book al 5.3%: c = 0.0505/(1-p)')
for p in [0.6,0.45,0.15]:
    print(f'    p={p}: c equivalente = {0.0505/(1-p)*100:.1f}%')

print('\n=== 4. Handicap asiatico a quarti: il payoff NON e binario ===')
print(' AH -0.25 = meta puntata su 0 (pareggio = rimborso), meta su -0.5')
p_win,p_draw,p_loss=0.45,0.27,0.28
oh=2.05
print(f' p(vince)={p_win} p(pari)={p_draw} p(perde)={p_loss}, quota {oh}')
print(' esiti del payoff per unita puntata:')
b=oh-1
pay={'vittoria':b, 'pareggio':b/2*1+(-1)/2*0 if False else 0.5*0+0.5*(-0)*0}
# corretto: meta linea 0 -> pareggio = rimborso (0); meta linea -0.5 -> pareggio = persa (-1)
payoffs=np.array([b, 0.5*0+0.5*(-1), -1.0])
probs=np.array([p_win,p_draw,p_loss])
print('   vittoria:',round(payoffs[0],4),'  pareggio:',round(payoffs[1],4),'(meta rimborsata, meta persa)  sconfitta:',payoffs[2])
print(f'   EV = {np.sum(probs*payoffs):+.5f}')
def negG2(f):
    w=1+payoffs*f
    if np.any(w<=1e-9): return 1e6
    return -np.sum(probs*np.log(w))
from scipy.optimize import minimize_scalar
res=minimize_scalar(negG2,bounds=(0,0.9),method='bounded')
f_bin=(p_win*oh-1)/b   # formula binaria che ignora il rimborso parziale
print(f'   Kelly corretto (3 esiti) = {res.x:.5f}')
print(f'   formula binaria ingenua  = {f_bin:.5f}   errore {f_bin/res.x:.3f}x')
