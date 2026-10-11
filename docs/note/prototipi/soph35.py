import numpy as np
from scipy import stats

print('=== 1. Relazione sofisticazione - risultato, a livello di MODELLO (n=8) ===')
mod=['Opus 4.6','GPT-5.4','GLM-5','Kimi K2.5','Trinity','Gemini 3.1 Pro','Grok 4.20','Gemini Flash Lite']
sop=np.array([32.6,31.8,22.0,15.9,12.1,9.8,9.8,6.1])
bank=np.array([89035,86365,41221,7420,np.nan,56715,np.nan,41605])
print(f'{"modello":22s}{"sofist.":>9s}{"bankroll finale":>18s}')
for m,s,b in zip(mod,sop,bank):
    print(f'{m:22s}{s:8.1f}%{("n/a" if np.isnan(b) else f"GBP {b:,.0f}"):>18s}')
ok=~np.isnan(bank)
r,p=stats.pearsonr(sop[ok],bank[ok]); rs,ps=stats.spearmanr(sop[ok],bank[ok])
print(f'\n escludendo i due n/a (n={ok.sum()}):')
print(f'   Pearson  r = {r:+.4f}  p = {p:.4f}')
print(f'   Spearman rho = {rs:+.4f}  p = {ps:.4f}')
# trattando n/a come rovina (bankroll 0)
b2=np.nan_to_num(bank,nan=0.0)
r2,p2=stats.pearsonr(sop,b2); rs2,ps2=stats.spearmanr(sop,b2)
print(f' trattando i due n/a come rovina, bankroll = 0 (n=8):')
print(f'   Pearson  r = {r2:+.4f}  p = {p2:.4f}')
print(f'   Spearman rho = {rs2:+.4f}  p = {ps2:.4f}')

print('\n=== 2. le inversioni, che sono il punto ===')
print(' Gemini 3.1 Pro: sofisticazione 9.8% ma bankroll GBP 56,715')
print(' GLM-5:          sofisticazione 22.0% ma bankroll GBP 41,221')
print(f' -> GLM-5 ha sofisticazione {22.0/9.8:.1f}x quella di Gemini Pro e un bankroll {41221/56715:.2f}x')
print(' Gemini Flash Lite: sofisticazione 6.1%, bankroll GBP 41,605 -> praticamente pari a GLM-5 (22.0%)')

print('\n=== 3. ancoraggio sulle baseline Dixon-Coles dell appendice D ===')
base={'(a) DC solo Premier League':7,'(b) DC multi-lega e coppe':7,'(c) DC mescolato col mercato':11}
for k,v in base.items():
    print(f'   {k:32s} {v:2d}/44 = {v/44*100:.0f}%')
print('   tutte e tre con Kelly frazionario f = 0.25 f*')
print(f'   la migliore, la (c), chiude a GBP 69,000: sopra tutti i modelli tranne Opus e GPT-5.4')
print()
print(' stima ancorata per l Agente C, partendo dalla (c) = 11/44:')
add=[('crit. 11 approccio speciale neopromosse',1),
     ('crit. 4a passaggio a modello state-space',1),
     ('criteri su non-stazionarieta (numero ignoto)','?')]
for a,v in add: print(f'   + {a:44s} {v}')
print(f'   -> stima MINIMA verificabile: 11 + 2 = 13/44 = {13/44*100:.0f}%')
print(f'      per confronto: Opus 4.6 = {32.6:.1f}%, GPT-5.4 = {31.8:.1f}%')
print(f'      soglia per superare Opus: {int(np.ceil(0.326*44))}/44')

print('\n=== 4. quanto della rubrica e pubblico ===')
print(' criteri totali: 38   punteggio massimo: 44   criteri pubblicati: 3')
print(f' copertura pubblica: {3/38*100:.1f}% dei criteri')
pub=2+2+1
print(f' punti coperti dai criteri pubblicati: {pub}/44 = {pub/44*100:.1f}%')
print(f' punti NON attribuibili senza la rubrica: {44-pub}/44 = {(44-pub)/44*100:.1f}%')
