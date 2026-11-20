"""Diagramma dello schema Structural-Hybrid per il capitolo 3 della tesi."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

out = sys.argv[1]
fig, ax = plt.subplots(figsize=(11, 5.6))
ax.set_xlim(0, 110)
ax.set_ylim(0, 56)
ax.axis("off")

BLUE, ORANGE, GREEN, GREY = "#dbe8f5", "#fbe3c8", "#d9efd9", "#eeeeee"


def box(x, y, w, h, title, body, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=color, ec="#333333", lw=1.2))
    ax.text(x + w / 2, y + h - 2.6, title, ha="center", va="top", fontsize=11.5, fontweight="bold")
    ax.text(x + w / 2, y + h - 7.2, body, ha="center", va="top", fontsize=9.3, linespacing=1.45)


def arrow(p, q, text="", dx=0.0, dy=1.2, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=16, lw=1.4,
                                 color="#333333", linestyle=ls))
    if text:
        ax.text((p[0] + q[0]) / 2 + dx, (p[1] + q[1]) / 2 + dy, text, ha="center", va="bottom",
                fontsize=8.8, style="italic")


box(2, 34, 22, 18, "Mercato e dati", "quote Bet365\nrisultati passati\n(solo informazioni\nprima della partita)", GREY)
box(32, 34, 28, 18, "1. Lavoratore", "modello Elo-Davidson\nprobabilità p̂ dei tre esiti\nregola di scelta dell'esito\nfrazione di Kelly f", BLUE)
box(70, 34, 36, 18, "Puntata", "puntata = λ · f · capitale\nλ = 0,25 senza allarme\nλ = 0,19 errore nei dati\nλ = 0,10 errore strutturale\n(finché dura l'allarme)", GREY)
box(32, 3, 28, 22, "2. Supervisore", "residuo δ = ln p̂(esito) − ln q(esito)\nultime 40 partite contro\nun periodo di riferimento\nANOVA sulla media\nANOVA sulla dispersione", ORANGE)
box(70, 3, 36, 22, "3. Ricalibratore", "solo se c'è allarme\nerrore atteso dalle caratteristiche\ndelle partite (stagione di calibrazione)\nBlinder-Oaxaca a due termini:\nerrore nei dati o strutturale", GREEN)

arrow((24.8, 43), (31.2, 43), "quote, calendario")
arrow((60.8, 43), (69.2, 43), "p̂, f")
arrow((46, 33.2), (46, 25.8), "esito osservato\ndopo la partita", dx=-9.5, dy=-2.8)
arrow((60.8, 14), (69.2, 14), "allarme")
arrow((88, 25.8), (88, 33.2), "λ", dx=2.5, dy=-1.5)
ax.text(46, 0.2, "riferimento: la stagione di calibrazione del modello",
        ha="center", va="bottom", fontsize=8.6, color="#444444")

fig.tight_layout()
fig.savefig(out, dpi=200)
print("saved", out)
