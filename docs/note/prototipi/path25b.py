import numpy as np
rng=np.random.default_rng(11)
print('=== barriera assorbente: la STESSA sequenza di esiti, ordini diversi ===')
n=120; f=0.30
r=np.where(rng.random(n)<0.55, f*1.0, -f)   # 1 vinta = +30%, persa = -30%
print(f' sequenza fissa: {np.sum(r>0)} vinte / {n}   B_T senza barriera = {np.prod(1+r):.6f}')
def with_floor(seq, floor=0.05):
    B=1.0
    for x in seq:
        if B<floor: return 0.0
        B*=(1+x)
    return B
vals=np.array([with_floor(r[rng.permutation(n)]) for _ in range(5000)])
print(f' con barriera a 0.05, su 5000 permutazioni:')
print(f'   rovinate: {np.mean(vals==0)*100:.1f}%   B_T mediano dei sopravvissuti: {np.median(vals[vals>0]):.6f}')
print(f'   -> stessi esiti, stesso numero di vittorie: l ORDINE decide chi sopravvive')

print('\n=== 5. P(drawdown) sotto Kelly frazionario: alpha^(2/lambda - 1) ===')
T=6000; p=0.52; o=2.0; fstar=(p*o-1)/(o-1); M=40_000
print(f' f* = {fstar:.4f}')
print(f'{"lambda":>7s}{"2/l-1":>7s}' + ''.join(f'{f"a={a}":>22s}' for a in [0.5,0.25,0.10]))
print(f'{"":14s}' + ''.join(f'{"teorico":>11s}{"simulato":>11s}' for _ in range(3)))
for lam in [1.0,0.5,0.25]:
    ff=lam*fstar; e=2/lam-1
    mn=np.ones(M)
    B=np.ones(M)
    for _ in range(T//500):
        W=rng.random((M,500))<p
        seg=np.cumprod(1+np.where(W,ff*(o-1),-ff),axis=1)*B[:,None]
        mn=np.minimum(mn,seg.min(1)); B=seg[:,-1]
    row=''
    for a in [0.5,0.25,0.10]:
        row+=f'{a**e:11.5f}{np.mean(mn<=a):11.5f}'
    print(f'{lam:7.2f}{e:7.1f}'+row)
print('\n -> Kelly pieno: P(scendere mai al 50%) = 50%. Mezzo: 12.5%. Quarto: 0.78%.')
