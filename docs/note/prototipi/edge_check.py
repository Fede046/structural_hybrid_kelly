import numpy as np
np.set_printoptions(precision=6, suppress=True)

# ---------- 1. f* = EV/b e sensibilita esatta ----------
def kelly(p, o):
    b = o - 1
    return (p*o - 1)/b

print('=== 1. f* = EV/b ===')
for p,o in [(0.55,2.0),(0.16,6.50),(0.40,2.70)]:
    b=o-1; EV=p*o-1
    print(f' p={p} o={o}  EV={EV:+.4f}  f*={kelly(p,o):+.6f}  EV/b={EV/b:+.6f}  p-(1-p)/b={p-(1-p)/b:+.6f}')

print('\n=== 2. c = f_hat/f* con p_hat = (1+eps)p : formula c = (1+eps) + eps/EV ===')
print(f'{"EV":>8s} {"eps=+10%":>12s} {"formula":>12s} {"eps=-10%":>12s} {"formula":>12s}')
for EV in [0.02,0.03,0.05,0.1111,0.15,0.30]:
    for o in [2.5]:
        p=(1+EV)/o; b=o-1
        for eps in [0.10]:
            c_num = kelly((1+eps)*p,o)/kelly(p,o)
            c_for = (1+eps)+eps/EV
            cn2 = kelly((1-eps)*p,o)/kelly(p,o)
            cf2 = (1-eps)-eps/EV
    print(f'{EV:8.4f} {c_num:12.4f} {c_for:12.4f} {cn2:12.4f} {cf2:12.4f}')
print(' soglia di raddoppio a eps=+10%:  EV < 1/9 =', round(1/9,6))
EV=1/9; o=2.5; p=(1+EV)/o
print('  verifica a EV=1/9 esatto: c =', round(kelly(1.1*p,o)/kelly(p,o),8))

print('\n=== 3. propagazione: Var(c) = o^2 Var(p_hat) / EV^2 ===')
rng=np.random.default_rng(1)
for o,EV,sp in [(2.5,0.03,0.02),(6.5,0.05,0.015),(1.8,0.02,0.01)]:
    p=(1+EV)/o; b=o-1
    ph=rng.normal(p,sp,2_000_000)
    fh=(ph*o-1)/b; fs=(p*o-1)/b
    c=fh/fs
    print(f' o={o} EV={EV} sd(p)={sp}:  Var(c) empirica={c.var():.6f}  formula={o**2*sp**2/EV**2:.6f}  E[c]={c.mean():.6f}')
