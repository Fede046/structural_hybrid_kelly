import numpy as np
rng=np.random.default_rng(29)

print('=== LE TRE SOGLIE IN FORMA CHIUSA ===')
print(' stake_t = max(F, lambda*f* * B_t).  Tre bankroll critici annidati:')
print('   B1 = F/(lambda f*)   il floor supera Kelly: la struttura moltiplicativa si rompe')
print('   B2 = F/(2 f*)        la puntata forzata ha crescita attesa NEGATIVA')
print('   B3 = F               non si puo piazzare la scommessa obbligatoria: rovina')
print(' nota: B2 NON dipende da lambda. B1 = B2 * 2/lambda.')
print()
def soglie(EV,o,lam,F):
    b=o-1; fs=EV/b
    return F/(lam*fs), F/(2*fs), F, fs
print(f'{"EV":>6s}{"o":>6s}{"f*":>8s}{"lambda":>8s}{"B1/F":>9s}{"B2/F":>9s}')
for EV,o,lam in [(0.03,2.5,0.25),(0.03,2.5,1.00),(0.05,2.5,0.25),(0.02,3.5,0.25),(0.03,2.5,0.10)]:
    B1,B2,B3,fs=soglie(EV,o,lam,1.0)
    print(f'{EV:6.2f}{o:6.1f}{fs:8.4f}{lam:8.2f}{B1:9.1f}{B2:9.1f}')

print('\n=== IL CONTO CHE DECIDE TUTTO: quanto vale B1 e B2 in % del bankroll iniziale ===')
print(' (EV=3%, o=2.5 -> f*=0.02; quarto-Kelly)')
print(f'{"B_0":>12s}{"floor F":>10s}{"B_0/F":>12s}{"B1 (rottura)":>15s}{"% di B_0":>11s}{"B2 (crescita<0)":>18s}{"% di B_0":>11s}')
for B0,F in [(100_000,0.01),(100_000,1.00),(220,0.01),(220,1.00),(1000,1.00)]:
    B1,B2,_,fs=soglie(0.03,2.5,0.25,F)
    print(f'{B0:12,.0f}{F:10.2f}{B0/F:12,.0f}{B1:15,.2f}{B1/B0*100:10.3f}%{B2:18,.2f}{B2/B0*100:10.3f}%')
print('\n -> con B_0=220 e F=1 la soglia di rottura e a 200, cioe il 91% del bankroll iniziale:')
print('    la struttura di Kelly e rotta quasi da subito.')
print(f'    verifica: quarto-Kelly iniziale = 0.25*0.02*220 = GBP {0.25*0.02*220:.2f}, appena sopra il floor di GBP 1')

print('\n=== SIMULAZIONE: stesso agente con e senza floor ===')
def run(B0,F,lam,EV,o,T,M,forced=True,seed=1):
    rg=np.random.default_rng(seed); b=o-1; fs=EV/b; p=(1+EV)/o
    B=np.full(M,float(B0)); alive=np.ones(M,bool); minB=B.copy()
    for t in range(T):
        want=lam*fs*B
        stake=np.maximum(want,F) if forced else want
        stake=np.minimum(stake,B)
        stake=np.where(alive,stake,0.0)
        win=rg.random(M)<p
        B=np.where(alive, B+np.where(win,stake*b,-stake), B)
        if forced: alive &= (B>=F)
        else:      alive &= (B>0)
        B=np.where(alive,B,0.0)
        minB=np.minimum(minB,np.where(alive,B,0.0))
    return B, alive
T=150; M=40000
print(f'{"scenario":34s}{"rovina":>9s}{"mediana B_T":>14s}{"q05":>10s}{"q95":>11s}')
for lbl,B0,F,forced in [('B0=100k, F=0.01, floor attivo',100_000,0.01,True),
                        ('B0=100k, senza floor',100_000,0.01,False),
                        ('B0=220,  F=0.01, floor attivo',220,0.01,True),
                        ('B0=220,  senza floor',220,0.01,False),
                        ('B0=220,  F=1.00, floor attivo',220,1.00,True)]:
    B,al=run(B0,F,0.25,0.03,2.5,T,M,forced)
    print(f'{lbl:34s}{(1-al.mean())*100:8.3f}%{np.median(B)/B0:14.4f}{np.quantile(B,0.05)/B0:10.4f}{np.quantile(B,0.95)/B0:11.4f}')
print(' (valori di B_T normalizzati sul bankroll iniziale)')
