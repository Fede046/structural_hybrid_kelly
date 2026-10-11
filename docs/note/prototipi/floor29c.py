import numpy as np
def run(B0,F,frac,EV,o,T,M,forced,seed=3,nbets=1):
    rg=np.random.default_rng(seed); b=o-1; p=(1+EV)/o
    B=np.full(M,float(B0)); alive=np.ones(M,bool)
    for t in range(T):
        for k in range(nbets):
            want=frac*B
            stake=np.maximum(want,F) if (forced and k==0) else want
            stake=np.minimum(stake,B); stake=np.where(alive,stake,0.0)
            win=rg.random(M)<p
            B=np.where(alive,B+np.where(win,stake*b,-stake),B)
            alive &= (B>=(F if forced else 1e-12)); B=np.where(alive,B,0.0)
    return B,alive

o=2.5; b=o-1; M=80000
print('=== TEST ISOLATO: agente GIA in difficolta, a 5*B1 ===')
print(' EV vero -2%, quarto-Kelly su edge stimato +3% -> f=0.005, B1=F/0.005=200F')
f=0.25*(0.03/b); F=1.0; B1=F/f
print(f' f={f:.4f}  B1={B1:.0f}F   partenza a 5*B1 = {5*B1:.0f}F')
print(f'{"orizzonte":>10s}{"rovina CON floor":>19s}{"rovina SENZA floor":>21s}{"rapporto":>11s}')
for T in [150,400,1000,3000]:
    _,a1=run(5*B1,F,f,-0.02,o,T,M,True)
    _,a0=run(5*B1,F,f,-0.02,o,T,M,False)
    r1=(1-a1.mean()); r0=(1-a0.mean())
    print(f'{T:10d}{r1*100:18.3f}%{r0*100:20.3f}%{(r1/max(r0,1e-9)):11.2f}x')

print('\n=== e partendo gia sotto la soglia di crescita negativa B2 = 25F ===')
B2=F/(2*(0.03/b))
print(f' B2={B2:.0f}F  partenza a 2*B2 = {2*B2:.0f}F')
print(f'{"orizzonte":>10s}{"rovina CON floor":>19s}{"rovina SENZA floor":>21s}{"rapporto":>11s}')
for T in [150,400,1000]:
    _,a1=run(2*B2,F,f,-0.02,o,T,M,True)
    _,a0=run(2*B2,F,f,-0.02,o,T,M,False)
    r1=(1-a1.mean()); r0=(1-a0.mean())
    print(f'{T:10d}{r1*100:18.3f}%{r0*100:20.3f}%{(r1/max(r0,1e-9)):11.2f}x')

print('\n=== agente aggressivo, 6 scommesse per giornata, Kelly pieno su edge sovrastimato ===')
print(' EV vero -4%, punta come se fosse +10% -> f=0.0667 per scommessa')
fa=0.10/b
for B0,F,lbl in [(100_000,0.01,'B0=100k F=0.01'),(220,1.00,'B0=220 F=1.00'),(220,0.01,'B0=220 F=0.01')]:
    _,a1=run(B0,F,fa,-0.04,o,150,M,True,nbets=6)
    _,a0=run(B0,F,fa,-0.04,o,150,M,False,nbets=6)
    print(f' {lbl:18s} rovina con floor {(1-a1.mean())*100:7.3f}%   senza floor {(1-a0.mean())*100:7.3f}%')

print('\n=== confronto con la formula analitica di 2.5: P(rovina) = alpha^(2/lambda-1) ===')
print(' alpha = F/B_0 ; lambda = frazione di Kelly EFFETTIVA rispetto al Kelly del vero EV')
print(' (vale solo con EV>0; con EV<0 la deriva e negativa e la rovina tende a 1 su orizzonte infinito)')
for B0,F,lam in [(220,1.0,0.25),(220,0.01,0.25),(100_000,0.01,0.25)]:
    a=F/B0; e=2/lam-1
    print(f'   B_0={B0:>7,} F={F:<5} alpha={a:.2e}  alpha^{e:.0f} = {a**e:.3e}')
