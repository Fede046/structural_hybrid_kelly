import numpy as np
rng=np.random.default_rng(7)

def Egrowth(lam, c, p, o, fstar, trunc):
    b=o-1
    f = lam*c*fstar
    if trunc: f = np.maximum(f, 0.0)
    f = np.minimum(f, 0.999)
    return np.mean(p*np.log(1+b*f) + (1-p)*np.log(1-f))

def study(o, EV, sp, trunc, N=400_000, label=''):
    p=(1+EV)/o; b=o-1; fstar=EV/b
    ph=rng.normal(p,sp,N)
    fh=(ph*o-1)/b
    if trunc: fh=np.maximum(fh,0.0)
    c=fh/fstar
    Ec, Ec2 = c.mean(), (c**2).mean()
    lam_naive = 1/(1+c.var())
    lam_gen   = Ec/Ec2
    grid=np.linspace(0.001,1.5,1500)
    g=[Egrowth(l,c,p,o,fstar,trunc) for l in grid]
    lam_num=grid[int(np.argmax(g))]
    print(f'{label:34s} E[c]={Ec:6.3f} Var(c)={c.var():7.3f} | naive={lam_naive:.4f}  E[c]/E[c2]={lam_gen:.4f}  numerico={lam_num:.4f}')
    return lam_naive, lam_gen, lam_num

print('=== lambda* : senza troncamento ===')
for o,EV,sp in [(2.5,0.05,0.01),(2.5,0.03,0.02),(6.5,0.05,0.015),(1.8,0.04,0.008)]:
    study(o,EV,sp,False,label=f'o={o} EV={EV} sd={sp} NO trunc')
print('\n=== lambda* : con troncamento f_hat = max(0, .) ===')
for o,EV,sp in [(2.5,0.05,0.01),(2.5,0.03,0.02),(6.5,0.05,0.015),(1.8,0.04,0.008)]:
    study(o,EV,sp,True,label=f'o={o} EV={EV} sd={sp} CON trunc')

print('\n=== crescita attesa a lambda=1 (Kelly pieno con rumore) : segno vs Var(c)=1 ===')
print(f'{"o":>5s}{"EV":>8s}{"sd(p)":>8s}{"Var(c)":>9s}{"E[G] full":>12s}{"E[G] lam*":>12s}')
for o,EV,sp in [(2.5,0.05,0.008),(2.5,0.05,0.012),(2.5,0.05,0.020),(2.5,0.05,0.030)]:
    p=(1+EV)/o;b=o-1;fstar=EV/b
    ph=rng.normal(p,sp,400_000); c=((ph*o-1)/b)/fstar
    vc=c.var(); lam=1/(1+vc)
    print(f'{o:5.1f}{EV:8.3f}{sp:8.3f}{vc:9.3f}{Egrowth(1,c,p,o,fstar,False):12.3e}{Egrowth(lam,c,p,o,fstar,False):12.3e}')
print('  soglia teorica: E[G] a lambda=1 cambia segno quando Var(c)=1, cioe sd(p)*o = EV')
for o,EV in [(2.5,0.05)]:
    print(f'  o={o} EV={EV} -> sd(p) critico = EV/o = {EV/o:.4f}')
