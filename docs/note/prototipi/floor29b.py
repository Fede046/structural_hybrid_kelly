import numpy as np
rng=np.random.default_rng(31)

def run(B0,F,frac_rule,EV,o,T,M,forced=True,seed=1):
    """frac_rule: funzione B -> frazione desiderata"""
    rg=np.random.default_rng(seed); b=o-1; p=(1+EV)/o
    B=np.full(M,float(B0)); alive=np.ones(M,bool)
    for t in range(T):
        want=frac_rule(B)*B
        stake=np.maximum(want,F) if forced else want
        stake=np.minimum(stake,B); stake=np.where(alive,stake,0.0)
        win=rg.random(M)<p
        B=np.where(alive,B+np.where(win,stake*b,-stake),B)
        alive &= (B>=(F if forced else 1e-12))
        B=np.where(alive,B,0.0)
    return B,alive

T=150; M=60000; o=2.5; b=o-1
print('=== CASO REALISTICO: edge NEGATIVO (g_hat<0), come nel benchmark ===')
print(' EV=-2%, quarto-Kelly su un edge STIMATO di +3% (il modello crede di avere edge)')
fstar=0.03/b
rule=lambda B: 0.25*fstar
print(f'{"scenario":36s}{"rovina":>10s}{"mediana B_T/B_0":>18s}{"q05":>10s}')
for lbl,B0,F,forced in [('B0=100k F=0.01  floor',100_000,0.01,True),
                        ('B0=100k         senza floor',100_000,0.01,False),
                        ('B0=220  F=0.01  floor',220,0.01,True),
                        ('B0=220  F=1.00  floor',220,1.00,True),
                        ('B0=220          senza floor',220,1e-12,False)]:
    B,al=run(B0,F,rule,-0.02,o,T,M,forced)
    print(f'{lbl:36s}{(1-al.mean())*100:9.4f}%{np.median(B)/B0:18.4f}{np.quantile(B,0.05)/B0:10.4f}')

print('\n=== CASO AGGRESSIVO: Kelly pieno su edge stimato +8% ma EV vero -4% ===')
print(' (ricalca i 5 modelli su 8 andati in rovina nel benchmark)')
rule2=lambda B: 1.0*(0.08/b)
print(f'{"scenario":36s}{"rovina":>10s}{"mediana B_T/B_0":>18s}{"q05":>10s}')
for lbl,B0,F,forced in [('B0=100k F=0.01  floor',100_000,0.01,True),
                        ('B0=100k         senza floor',100_000,1e-12,False),
                        ('B0=220  F=1.00  floor',220,1.00,True),
                        ('B0=220          senza floor',220,1e-12,False)]:
    B,al=run(B0,F,rule2,-0.04,o,T,M,forced)
    print(f'{lbl:36s}{(1-al.mean())*100:9.4f}%{np.median(B)/B0:18.6f}{np.quantile(B,0.05)/B0:10.6f}')

print('\n=== "SMETTI DI PUNTARE": costo della sola puntata minima obbligatoria ===')
print(' l agente misura g_hat<0 e punta solo il floor, 150 giornate, EV vero -5%')
print(f'{"B_0":>10s}{"F":>8s}{"esposizione totale":>21s}{"perdita attesa":>17s}{"% di B_0":>11s}{"rovina":>10s}')
for B0,F in [(100_000,0.01),(100_000,1.00),(220,0.01),(220,1.00)]:
    rule3=lambda B: 0.0
    B,al=run(B0,F,rule3,-0.05,o,T,M,True)
    tot=T*F; loss=tot*0.05
    print(f'{B0:10,.0f}{F:8.2f}{tot:21,.2f}{loss:17,.2f}{loss/B0*100:10.3f}%{(1-al.mean())*100:9.3f}%')
