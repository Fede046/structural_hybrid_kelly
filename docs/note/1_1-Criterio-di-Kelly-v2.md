---
Titolo: "A New Interpretation of Information Rate"
autore: John L. Kelly Jr.
rivista: Bell System Technical Journal
data pubblicazione: 1956-07 (vol. 35, n. 4, pp. 917–926)
doi: 10.1002/j.1538-7305.1956.tb03809.x
tags: [kelly-criterion, money-management, portfolio-theory, gambling-theory, information-theory, risk-of-ruin, appunti-universitari]
versione: 2.0
data-revisione: 2026-08-20
collegato-a: "[[todo_prerequisiti_tesi_v2]]"
---


# 1.1 Criterio di Kelly

> [!info]+ Revisione v2 — cosa è cambiato
> **Correzioni:** esempio numerico della media geometrica (§1.3, era 0,1 invece di 0,1489); precisazione nat/bit (§3.4); box sulle tre quantità chiamate $\sigma^2$ (§5.2); $c=1/\gamma$ è **esatto** nel modello diffusivo, non approssimato (§6.4); caveat sulla validità diffusiva della tabella (§8.3).
> **Sezioni nuove:** §4.4 formulazione in divergenza KL · §6.5 tasso di crescita certo-equivalente · §7 Kelly multi-esito e scommesse simultanee · §10 ponti verso la tesi.
> **Rinumerazione:** la vecchia §7 (rischio di rovina) è ora §8, la vecchia §8 (Samuelson) è ora §9, la checklist è ora §11.

## 0. Perché questo argomento è importante

Il criterio di Kelly nasce nel 1956 all'interno dei Bell Labs, **non** come strumento di finanza o di scommesse, ma come sotto-prodotto della teoria dell'informazione di Shannon. Kelly stava cercando un'interpretazione "fisica" e operativa del *rate* di trasmissione dell'informazione $R$, e la trovò immaginando un giocatore che riceve, tramite un canale rumoroso, informazioni privilegiate sull'esito di scommesse (es. corse di cavalli truccate comunicate via un canale con errori). Il risultato sorprendente: ==**il tasso di crescita esponenziale ottimale del capitale del giocatore coincide numericamente con il tasso di trasmissione dell'informazione del canale**==.

> [!important] Da tenere a mente
> Il criterio di Kelly **non nasce come criterio di gestione del rischio finanziario**: è un *teorema di teoria dell'informazione riletto in chiave di crescita del capitale*. La sua adozione in finanza (Thorp) e nel gioco d'azzardo è un'estensione successiva, concettualmente solida ma logicamente indipendente dalla motivazione originaria di Kelly.

---

## 1. Impostazione formale del problema

### 1.1 Il modello base (scommessa binaria ripetuta)

Consideriamo un giocatore con capitale iniziale $X_0$ che scommette ripetutamente su un evento con due esiti:

- vince con probabilità $p$;
- perde con probabilità $q = 1-p$.

==Ad ogni turno il giocatore punta una **frazione** $f$ del proprio capitale corrente (non un importo fisso==: questo è cruciale, è ciò che rende il processo **moltiplicativo** e non additivo).

Le quote sono espresse come **"b to 1"**: se vince, riceve $b$ volte la posta puntata (oltre a riavere la posta), se perde, perde l'intera posta.

Formalmente, il capitale evolve come:

$$
X_n =
\begin{cases}
X_{n-1}\,(1+f b) & \text{con probabilità } p \quad (\text{vittoria}) \\
X_{n-1}\,(1-f) & \text{con probabilità } q \quad (\text{sconfitta})
\end{cases}
$$

### 1.2 Perché il processo è moltiplicativo e non additivo

Ogni puntata è una frazione del capitale *corrente*, non del capitale iniziale. Questo significa che il capitale dopo $n$ turni è un **prodotto** di fattori casuali:

$$
X_n = X_0 \prod_{i=1}^n R_i, \qquad R_i \in \{1+fb,\ 1-f\}
$$

> [!note] Commento
> Questa struttura moltiplicativa è la ragione profonda per cui la **media aritmetica** non è la quantità giusta da massimizzare (vedi §5.2). Un processo moltiplicativo con un solo fattore nullo (o negativo abbastanza) azzera tutto il percorso futuro: da qui l'interesse per la **media geometrica**, che è l'unica misura di tendenza centrale coerente con la composizione moltiplicativa.
> 

### 1.3 Richiamo: la media geometrica

**Definizione**

La **media geometrica** di _n_ numeri positivi è quel valore che, moltiplicato per se stesso _n_ volte, dà lo stesso prodotto dei numeri di partenza. In altre parole, è la radice _n_-esima del prodotto degli _n_ valori considerati.

Si usa tipicamente quando i dati rappresentano **tassi di variazione, rapporti o crescite percentuali** (ad esempio tassi di interesse composto, tassi di crescita annuali, indici), a differenza della media aritmetica che è più adatta a sommare quantità dello stesso tipo.

**Formula**

Per _n_ numeri positivi $x_1, x_2, \ldots, x_n$:

$$ G = \sqrt[n]{x_1 \cdot x_2 \cdot x_3 \cdots x_n} = \left( \prod_{i=1}^{n} x_i \right)^{1/n} $$

**Nota:** è definita solo per numeri positivi (o comunque non negativi), altrimenti la radice potrebbe non esistere nei numeri reali.

#### Formula alternativa (logaritmica)

Utile quando i numeri sono molti o molto grandi, per evitare overflow nei calcoli:

$$ G = \exp\left( \frac{1}{n} \sum_{i=1}^{n} \ln x_i \right) $$

**Esempio pratico**

Calcoliamo la media geometrica di 2, 8 e 4:

$$ G = \sqrt[3]{2 \cdot 8 \cdot 4} = \sqrt[3]{64} = 4 $$

**Confronto con la media aritmetica**

Per lo stesso insieme di dati, vale sempre:

$$ G \leq A $$

dove _A_ è la media aritmetica, con uguaglianza solo se tutti i valori sono identici (disuguaglianza AM-GM).

**Esempio d'uso tipico**: se un investimento cresce del 10% il primo anno e del 20% il secondo anno, il tasso di crescita medio annuo non si calcola con la media aritmetica (15%), ma con quella geometrica:

$$G = \sqrt{1{,}10 \cdot 1{,}20} - 1 = \sqrt{1{,}32} - 1 \approx 0{,}1489$$

cioè **≈ 14,89%** annuo, non 15%. La differenza è piccola ma sistematica e sempre nello stesso verso ($G \le A$): il capitale finale è $1{,}1489^2 = 1{,}32$, esattamente il prodotto di partenza, mentre usando il 15% si otterrebbe $1{,}15^2 = 1{,}3225$, cioè una crescita che non è mai avvenuta.

Questo perché la crescita composta è un fenomeno moltiplicativo, non additivo.

---

## 2. Derivazione della formula di Kelly (massimizzazione dell'utilità logaritmica)

### 2.1 La funzione obiettivo: tasso di crescita atteso

Definiamo il **tasso di crescita per periodo** come il valore atteso del logaritmo del fattore di crescita:

$$
g(f) \;=\; \mathbb{E}\left[\ln \frac{X_n}{X_{n-1}}\right] \;=\; p \ln(1+fb) + q \ln(1-f)
$$

Questa è, a tutti gli effetti, un'**utilità logaritmica** $U(X) = \ln X$ applicata alla ricchezza per-periodo. Due giustificazioni distinte portano a questa stessa funzione:

1. **Giustificazione "utilitaristica" (Bernoulli, 1738):** $\ln X$ è una funzione di utilità con avversione al rischio relativa costante (CRRA) pari a 1; un investitore con questa utilità sceglie sempre la frazione $f$ che massimizza $\mathbb{E}[\ln X_n]$.
2. **Giustificazione "asintotica" (Kelly stesso, poi Breiman 1961):** massimizzare $g(f)$ massimizza, **con probabilità 1**, il tasso di crescita esponenziale di lungo periodo del capitale — indipendentemente da qualunque preferenza soggettiva per il rischio. Questa seconda giustificazione è più forte perché non richiede di assumere che il giocatore abbia effettivamente utilità logaritmica: è una conseguenza della legge dei grandi numeri (vedi §5).

### 2.2 Condizione del primo ordine

Deriviamo $g(f)$ rispetto a $f$ e poniamo la derivata uguale a zero:

$$
\frac{dg}{df} = \frac{pb}{1+fb} - \frac{q}{1-f} = 0
$$

Risolviamo:

$$
pb(1-f) = q(1+fb)
$$
$$
pb - pbf = q + qfb
$$
$$
pb - q = pbf + qfb = fb(p+q)
$$

Poiché $p+q=1$:

$$
pb - q = fb \quad \Longrightarrow \quad \boxed{f^{*} = \dfrac{bp - q}{b} = p - \dfrac{q}{b}}
$$

Questa è **la formula di Kelly**.

### 2.3 Verifica della condizione del secondo ordine (concavità)

$$
\frac{d^2g}{df^2} = -\frac{pb^2}{(1+fb)^2} - \frac{q}{(1-f)^2} < 0 \quad \text{per ogni } f \text{ ammissibile}
$$

La derivata seconda è **sempre strettamente negativa**: $g(f)$ è strettamente concava sull'intero dominio ammissibile, quindi il punto critico $f^{*}$ è un **massimo globale** (non serve verificare condizioni al bordo separatamente, ma si nota che $g(0)=0$ e $g\to -\infty$ per $f\to 1^-$ se $q>0$, il che conferma la forma "a campana" di $g$).

> [!note] Commento sulla struttura della dimostrazione
> È interessante notare che la concavità di $g(f)$ non dipende in alcun modo dai valori di $p,q,b$: **il logaritmo è concavo ovunque**, quindi qualunque combinazione lineare di logaritmi di funzioni affini in $f$ eredita la concavità. Questo è il motivo strutturale per cui l'ottimizzazione ha sempre soluzione unica e ben definita, a differenza di funzioni obiettivo basate sulla ricchezza attesa (lineari in $f$, quindi prive di massimo interno — vedi §5.2).

---

## 3. La formula base $f^{*} = (bp-q)/b$: lettura e casi particolari

### 3.1 Interpretazione dei termini

- $bp - q$ è il **valore atteso del payoff per unità di posta** (l'"edge" o vantaggio): $\mathbb{E}[\text{payoff}] = p\cdot b + q \cdot(-1) = bp-q$.
- Dividere per $b$ normalizza l'edge alla scala delle quote: $f^{*} = p - q/b$ si legge anche come *"la probabilità di vincita, corretta per il rischio implicito nelle quote"*.

### 3.2 Condizione di scommessa positiva

$$
f^{*} > 0 \iff bp > q \iff \mathbb{E}[\text{payoff per unità puntata}] > 0
$$

Se $bp \le q$ (vantaggio nullo o negativo), la formula darebbe $f^{*}\le 0$: la prescrizione corretta è **non scommettere affatto** ($f=0$). Il criterio di Kelly non "corregge" mai una scommessa sfavorevole — semplicemente non gioca.

### 3.3 Caso particolare: quote alla pari ($b=1$)

$$
f^{*} = p - q = 2p - 1
$$

Interpretazione immediata: la frazione ottimale è semplicemente il doppio del vantaggio probabilistico rispetto al 50%.

### 3.4 Tasso di crescita massimo nel caso $b=1$

$$
g(f^{*}) = p\ln(2p) + q\ln(2q) = \ln 2 + p\ln p + q\ln q = \ln 2 - H(p)
$$

dove $H(p) = -p\ln p - q \ln q$ è l'**entropia binaria**. Questo chiude il cerchio con la motivazione originaria di Kelly: il tasso di crescita ottimale del capitale eguaglia esattamente il *rate* di informazione del canale — da cui il titolo del paper del 1956, *"A New Interpretation of Information Rate"*.

> [!warning] Attenzione all'unità di misura
> Scritta con $\ln$, l'espressione $g(f^{*}) = \ln 2 - H(p)$ è in **nat**, non in bit. Per leggere il risultato nella forma "informazione" bisogna usare i logaritmi in base 2 dappertutto (sia in $g$ sia in $H$):
> $$g_2(f^{*}) = 1 - H_2(p) \quad \text{[bit per scommessa]}$$
> dove $H_2(p) = -p\log_2 p - q\log_2 q$. In questa forma il risultato si legge come: *il tasso di crescita esponenziale ottimale del capitale, misurato in bit per giocata, è pari alla capacità informativa residua del canale*. È lo stesso numero, ma solo la versione in base 2 giustifica l'affermazione «la crescita del capitale **è** l'informazione». All'orale è una distinzione che vale la pena fare da soli prima che la faccia il relatore.

---

## 4. Ottimalità asintotica: perché massimizzare $g(f)$ è la scelta "giusta"

### 4.1 Legge dei grandi numeri applicata al log-capitale

Per la legge forte dei grandi numeri, dato che $\ln(X_n/X_0) = \sum_{i=1}^n \ln(X_i/X_{i-1})$ è una somma di variabili i.i.d.:

$$
\frac{1}{n}\ln\frac{X_n}{X_0} \xrightarrow[n\to\infty]{\text{q.c.}} g(f)
$$

Cioè, **con probabilità 1**:

$$
X_n \sim X_0 \, e^{n\, g(f)}
$$

Massimizzare $g(f)$ significa quindi massimizzare il tasso esponenziale con cui il capitale cresce **quasi certamente** nel lungo periodo. Questo è il celebre risultato di **Breiman (1961)**: la strategia di Kelly batte, con probabilità che tende a 1 al crescere del numero di giocate, qualunque altra strategia "essenzialmente diversa" — nel senso che $X_n^{\text{Kelly}}/X_n^{\text{altra strategia}} \to \infty$ q.c.

### 4.2 Il tranello: massimizzare $g(f)$ NON è come massimizzare la ricchezza attesa

$$
\mathbb{E}[X_n/X_{n-1}] = p(1+fb) + q(1-f) = 1 + f(pb - q)
$$

Questa espressione è **lineare** in $f$: se l'edge $bp-q$ è positivo, è massimizzata da $f=1$ (puntare tutto il capitale ad ogni turno).

> [!important] Commento — un paradosso centrale da capire bene
> Puntare $f=1$ ad ogni turno **massimizza la ricchezza media attesa**, ma porta alla **rovina certa** con probabilità 1 nel lungo periodo (basta una sola sconfitta, evento certo con $q>0$, per azzerare tutto). Il criterio di Kelly risolve questo paradosso lavorando non sulla media *aritmetica* della ricchezza, ma sulla media *geometrica* (equivalentemente: sulla media aritmetica del *logaritmo* della ricchezza). Questo è il nucleo concettuale dell'intero argomento: **massimizzare $\mathbb{E}[X_n]$ e massimizzare la crescita tipica/quasi-certa di $X_n$ sono obiettivi diversi**, e solo il secondo è coerente con un processo moltiplicativo ripetuto nel tempo.

### 4.3 Limite della giustificazione asintotica: la critica di Samuelson

La giustificazione di Breiman è **asintotica** ($n\to\infty$). Paul Samuelson ha criticato duramente l'uso pratico del criterio proprio su questo punto (vedi §9): per un orizzonte finito, massimizzare $\mathbb{E}[\ln X_N]$ non è equivalente a massimizzare l'utilità attesa di un investitore con una generica funzione di utilità, nemmeno se l'investitore è molto avverso al rischio e ha un orizzonte lungo. "Lungo periodo" non è una giustificazione automatica: va sempre chiarito *quanto* lungo, e rispetto a *quale* funzione obiettivo dell'investitore.

### 4.4 Formulazione in divergenza: da dove viene *davvero* la crescita

Il §3.4 mostra il legame con l'entropia nel caso particolare $b=1$ e senza mercato. Esiste però una forma generale, e molto più utile, che vale con un mercato che quota le probabilità.

Siano:

- $p^{*}$ la distribuzione **vera** degli esiti;
- $q$ la distribuzione **implicita nelle quote** di mercato ($q(x) = 1/\text{quota}(x)$, normalizzata);
- $p$ la distribuzione **stimata dal mio modello**, quella con cui dimensiono le puntate.

Se dimensiono le scommesse secondo Kelly rispetto alle mie credenze $p$, il tasso di crescita atteso del capitale è:

$$
g(p;\,p^{*},q) \;=\; \sum_x p^{*}(x)\,\ln\frac{p(x)}{q(x)} \;=\; \underbrace{D_{KL}(p^{*}\|q)}_{\text{errore del mercato}} \;-\; \underbrace{D_{KL}(p^{*}\|p)}_{\text{errore mio}}
$$

> [!important] Il risultato più importante di tutti gli appunti, ai fini della tesi
> La crescita è positiva **se e solo se il mio modello è più vicino alla verità di quanto lo sia il mercato**. Non "se il mio modello è buono": se è *più buono di quello implicito nelle quote*.
>
> Tre conseguenze operative, tutte non negoziabili:
> 1. **Nessuna regola di staking può creare edge.** Il dimensionamento della puntata non compare in questa espressione: $D_{KL}(p^{*}\|q)$ e $D_{KL}(p^{*}\|p)$ dipendono solo dal mercato e dal modello. Scegliere $f$, o una frazione $c$, o una regola di ricalibrazione sofisticata, agisce sulla *varianza del percorso* e sul *rischio di rovina*, **mai** sul segno del valore atteso. Se $D_{KL}(p^{*}\|p) > D_{KL}(p^{*}\|q)$, l'unica azione che porta $g$ a zero invece che a un valore negativo è **non scommettere**.
> 2. **La quantità da misurare empiricamente è una differenza di log-loss.** $D_{KL}(p^{*}\|p) - D_{KL}(p^{*}\|q)$ è stimabile direttamente come differenza tra il log-loss del modello e il log-loss del mercato sugli esiti realizzati (i termini di entropia di $p^{*}$ si cancellano). Questo è esattamente il confronto 0,974 vs 0,971 che uno dei modelli di frontiera valutati su KellyBench ha calcolato prima di ridurre le puntate al minimo: aveva verificato che $g<0$ e ha agito di conseguenza. È il test che va fatto **prima** di qualunque esperimento sul dimensionamento.
> 3. **L'overround del bookmaker entra qui.** Con un vig del 5,3%, $q$ non normalizzata somma a $\approx 1{,}053$: il mercato è deliberatamente *sbagliato* nella direzione sfavorevole allo scommettitore, e $D_{KL}(p^{*}\|q)$ va calcolata sulle probabilità normalizzate, tenendo presente che il margine è una tassa deterministica che si somma a ogni giocata.

**Collegamento con il §3.4.** Nel caso senza mercato, $q$ è la distribuzione uniforme indotta dalle quote alla pari e la formula collassa in $\ln 2 - H(p^{*})$: il §3.4 è il caso particolare di questa espressione. La forma in divergenza è quindi la generalizzazione corretta del risultato originale di Kelly a un contesto in cui esiste una controparte che quota.

---

## 5. Perché il Full Kelly è ad altissima varianza: la "volatilità di crescita"

### 5.1 Il paradosso apparente

Kelly massimizza il tasso di crescita **atteso** (nel senso di media, e asintoticamente quasi certo), ma questo non significa affatto che il percorso sia poco volatile. Anzi: **la frazione di Kelly a piena size è tipicamente associata a oscillazioni di capitale enormi**, inclusi drawdown (perdite dal massimo) molto profondi, anche in presenza di edge positivo e anche se, alla fine, il capitale cresce.

Definiamo la **varianza del tasso di crescita per periodo**:

$$
\sigma^2(f) = \mathrm{Var}\big[\ln(X_n/X_{n-1})\big] = pq\,\big[\ln(1+fb) - \ln(1-f)\big]^2
$$

Il punto cruciale è che $f^{*}$ **massimizza la media** $g(f)$ ma **non minimizza** $\sigma^2(f)$: nel punto di ottimo la varianza resta tipicamente molto elevata. Il Kelly pieno è quindi, nel gergo della disciplina, una strategia "growth-optimal" ma non "risk-averse": persegue solo la crescita, senza alcun peso esplicito sulla dispersione del percorso.

### 5.2 L'approssimazione diffusiva (tempo continuo) e la relazione $g = \sigma^2/2$

> [!caution] Nota sulla notazione — da tenere ben distinta
> Da qui in poi convivono **tre** quantità che si chiamano tutte "sigma quadro". Confonderle è il modo più rapido di sbagliare i conti del §8:
> - $\sigma^2(f)$ del **§5.1**: varianza del *log*-rendimento per periodo, nel modello **discreto** binario, $= pq[\ln(1+fb)-\ln(1-f)]^2$;
> - $\sigma^2$ del **§5.2**: volatilità per unità di tempo dell'**attività sottostante** nel modello diffusivo (parametro esogeno del moto browniano geometrico);
> - $\sigma^2_{\text{portafoglio}}(f) = f^2\sigma^2$: varianza del rendimento **del portafoglio** alla frazione $f$.
>
> Le relazioni notevoli $\sigma^2_{\text{portafoglio}}(f^{*}) = 2g(f^{*})$ e $P = a^{2g/\sigma^2}$ usano **la terza**, non la prima. Numericamente, nel modello diffusivo la varianza del log-ricchezza per unità di tempo coincide con $\sigma^2_{\text{portafoglio}}$ (entrambe valgono $f^2\sigma^2$), ed è questo che rende lecito il passaggio dal §5.2 al §5.3. Nel modello discreto la coincidenza vale solo approssimativamente, per $f$ piccolo.

Per capire *quantitativamente* quanto sia elevata questa volatilità, è utile passare al modello di tempo continuo (analogo al problema di Merton), che è lo strumento standard usato in letteratura (es. Sid Browne) per studiare i drawdown della strategia di Kelly. Supponiamo che l'attività su cui si investe una frazione $f$ del capitale abbia rendimento medio $\mu$ e volatilità $\sigma$ per unità di tempo (moto Browniano geometrico):

$$
\frac{dW}{W} = f\mu\, dt + f\sigma\, dZ
$$

Per il lemma di Itô, il tasso di crescita del logaritmo della ricchezza è:

$$
g(f) = f\mu - \frac{f^2\sigma^2}{2}
$$

Massimizzando rispetto a $f$:

$$
\frac{dg}{df} = \mu - f\sigma^2 = 0 \quad\Longrightarrow\quad f^{*} = \frac{\mu}{\sigma^2}
$$

(questa è la versione "a tempo continuo" della formula di Kelly: $f^{*} = \mu/\sigma^2$, l'analogo esatto di $(bp-q)/b$ nel limite di scommesse piccole e frequenti).

Sostituendo $f^{*}$ nella varianza del **portafoglio** (non del log-rendimento) alla frazione ottimale:

$$
\sigma^2_{\text{portafoglio}}(f^{*}) = (f^{*})^2 \sigma^2 = f^{*}\cdot(f^{*}\sigma^2) = f^{*}\mu
$$

E il tasso di crescita ottimo è:

$$
g(f^{*}) = f^{*}\mu - \frac{f^{*}\mu}{2} = \frac{f^{*}\mu}{2}
$$

Confrontando le due espressioni si ottiene la relazione notevole:

$$
\boxed{\sigma^2_{\text{portafoglio}}(f^{*}) = 2\, g(f^{*})}
$$

> [!important] Commento — il risultato più rilevante del paragrafo
> **Alla frazione di Kelly ottimale, la varianza del rendimento del portafoglio è esattamente il doppio del tasso di crescita che si sta massimizzando.** Non è un caso o un'approssimazione grossolana: è una conseguenza matematica diretta della condizione del primo ordine. Questo spiega *perché* il Kelly pieno è strutturalmente rumoroso: l'ottimizzazione stessa "spinge" la size fino al punto in cui il rischio (varianza) è proporzionale, con fattore 2, alla crescita ottenuta. Non esiste un modo di avere il tasso di crescita massimo di Kelly con una volatilità sostanzialmente più bassa: sono legate per costruzione.

### 5.3 Drawdown: la probabilità di "cadute" profonde anche con edge positivo

Usando l'approssimazione diffusiva, il logaritmo della ricchezza $Y_t=\ln(W_t/W_0)$ è un moto Browniano con drift $g$ e volatilità $\sigma$. Per un moto Browniano con drift positivo, la probabilità che tocchi mai un livello $-c$ (con $c>0$) è un risultato classico di teoria delle probabilità di primo passaggio:

$$
P(\text{tocca mai } -c) = e^{-2gc/\sigma^2}
$$

L'evento "il capitale cade a una frazione $a<1$ del capitale attuale" corrisponde a $c = \ln(1/a)$, quindi:

$$
P(\text{cade mai a frazione } a) = e^{-\frac{2g}{\sigma^2}\ln(1/a)} = a^{\,2g/\sigma^2}
$$

Alla frazione di Kelly piena, sappiamo dal §5.2 che $2g/\sigma^2 = 1$, quindi:

$$
\boxed{P(\text{Full Kelly cade mai a frazione } a) = a}
$$

**Esempio concreto:** per un giocatore in Full Kelly, la probabilità che il capitale scenda **a metà** del suo valore, prima o poi, nel corso del gioco, è **esattamente il 50%** — indipendentemente dall'edge specifico o dalle quote! Questo è un risultato controintuitivo ma ben documentato nella letteratura (Thorp; MacLean-Ziemba-Blazenko, 1992): un edge positivo garantisce crescita nel lunghissimo periodo, ma non protegge affatto da drawdown enormi lungo il percorso.

### 5.4 Il limite di non-ritorno: oltre 2×Kelly la crescita diventa negativa

Dalla formula $g(f) = f\mu - f^2\sigma^2/2$, ponendo $g(f)=0$ si trovano due soluzioni: $f=0$ e $f = 2\mu/\sigma^2 = 2f^{*}$.

> [!important] Commento — errore pratico molto comune
> Per $0<f<2f^{*}$ il tasso di crescita è positivo; oltre $f=2f^{*}$ (cioè oltre il **doppio** della size di Kelly) il tasso di crescita **diventa negativo**, anche se la scommessa singola ha ancora valore atteso positivo! Puntare più del doppio della size di Kelly non è "più aggressivo ma redditizio": è una strategia che conduce a rovina quasi certa nel lungo periodo, nonostante l'edge positivo. Questo evidenzia quanto sia sensibile il criterio agli errori di stima di $p$ (o di $\mu,\sigma$): sovrastimare l'edge porta facilmente a un "over-betting" pericoloso.

---

## 6. Kelly frazionario (Fractional Kelly)

### 6.1 Definizione

Si definisce **Kelly frazionario di livello $c$** (con $0<c<1$) la strategia che punta:

$$
f_c = c \cdot f^{*}
$$

Casi tipici: $c=0.5$ ("Half-Kelly"), $c=0.25$ ("Quarter-Kelly").

### 6.2 Perché conviene: il trade-off crescita/varianza

Usando ancora l'approssimazione diffusiva del §5.2, si può calcolare **esattamente** come si comportano crescita e varianza al variare di $c$.

**Tasso di crescita a frazione $c$:**

$$
g(cf^{*}) = cf^{*}\mu - \frac{c^2(f^{*})^2\sigma^2}{2}
$$

Sostituendo $f^{*}\sigma^2=\mu$ e semplificando (passaggi analoghi al §5.2):

$$
\boxed{g(cf^{*}) = g(f^{*})\cdot c(2-c)}
$$

**Varianza del portafoglio a frazione $c$:**

$$
\sigma^2_{\text{portafoglio}}(cf^{*}) = c^2 \cdot \sigma^2_{\text{portafoglio}}(f^{*})
$$

cioè la **volatilità** (deviazione standard) scala linearmente con $c$, mentre la **crescita residua** scala secondo $c(2-c)$ — una funzione concava che decresce più lentamente della volatilità.

### 6.3 Il caso Half-Kelly: il compromesso "classico"

Per $c=0.5$:

- crescita mantenuta: $g(0.5f^{*}) = g(f^{*})\cdot 0.5\,(2-0.5) = 0.75\, g(f^{*})$ → **75% della crescita massima**
- volatilità: $\sigma(0.5f^{*}) = 0.5\,\sigma(f^{*})$ → **50% della volatilità (deviazione standard) del Full Kelly**

> [!note] Commento — perché l'Half-Kelly è così popolare in pratica
> Con metà della size si ottiene il **75% della crescita** pagando solo la **metà della volatilità**. Questo rapporto asimmetrico e favorevole (rinuncio al 25% di crescita per dimezzare il rischio) è la ragione quantitativa, non solo intuitiva, per cui praticamente tutta la letteratura pratica (Thorp, MacLean-Ziemba) raccomanda di operare **sotto** il Kelly pieno, tipicamente tra 1/4 e 1/2 di Kelly. Il Kelly pieno è teoricamente ottimo solo rispetto a un unico criterio (la crescita attesa asintotica); appena si introduce una qualunque preferenza per la stabilità del percorso, una frazione minore diventa preferibile.

### 6.4 Perché il Kelly frazionario, in generale (non solo il caso $c=0.5$)

Le ragioni per adottare un Kelly frazionario nella pratica sono molteplici e complementari:

1. **Incertezza nella stima dei parametri.** $p$, $b$ (o $\mu,\sigma$) non sono mai noti con certezza ma stimati; un errore di stima verso l'alto dell'edge reale può portare, con Full Kelly, a un "over-betting" pericoloso (§5.4). Ridurre la size è una forma di robustezza rispetto all'incertezza parametrica.
2. **Utilità individuale diversa dal log.** Un investitore con avversione al rischio maggiore di quella implicita nell'utilità logaritmica (CRRA = 1) sceglierà razionalmente un $c<1$: il Kelly frazionario si deriva come ottimo per un'utilità CRRA generica $U(X)=X^{1-\gamma}/(1-\gamma)$, con $c = 1/\gamma$. ⚠️ **Nel modello diffusivo del §5.2 questa relazione è esatta, non approssimata**: massimizzando $\mathbb{E}[U(W_T)]$ sotto moto browniano geometrico si ottiene $f^{\dagger} = \mu/(\gamma\sigma^2) = f^{*}/\gamma$. È solo nel caso binario discreto che $c = 1/\gamma$ diventa un'approssimazione valida per piccoli edge. Vale la pena essere precisi su questo punto, perché rende l'argomento più forte: l'Half-Kelly non è un'euristica prudenziale, è **l'ottimo esatto** di un decisore con $\gamma = 2$.
3. **Riduzione della probabilità di drawdown severi** (§5.3 e §8): la relazione fra $c$ e la probabilità di una grande perdita non è lineare, ma **fortemente convessa a favore di $c$ minori** (vedi tabella al §8.3).

### 6.5 Tasso di crescita certo-equivalente: come confrontare strategie con $c$ diversi

I §6.2–6.3 danno crescita e volatilità **separatamente**. Ma questo lascia irrisolto il problema pratico del confronto: se la strategia X cresce del 4% annuo con volatilità 20% e la strategia Y cresce del 3% con volatilità 10%, quale è migliore? Le due colonne della tabella non rispondono — serve una metrica che le comprima in un unico numero.

**Definizione.** Il tasso di crescita certo-equivalente $g_{CE}$ è il tasso di crescita *deterministico* che il decisore giudicherebbe equivalente alla strategia rischiosa considerata. Nel modello diffusivo, per un decisore con avversione relativa al rischio $\gamma$:

$$
\boxed{g_{CE}(f) \;=\; f\mu - \frac{\gamma\, f^2 \sigma^2}{2}}
$$

Si noti che per $\gamma=1$ si ricade esattamente in $g(f) = f\mu - f^2\sigma^2/2$: **la crescita logaritmica di Kelly è già un certo-equivalente**, quello di un decisore con $\gamma=1$. Il Kelly pieno non è "neutrale al rischio", è ottimale per una specifica e ben identificata avversione al rischio. Questa è, detto in altri termini, la stessa osservazione di Samuelson (§9).

**In funzione della frazione $c$.** Sostituendo $f = c f^{*} = c\mu/\sigma^2$:

$$
g_{CE}(cf^{*}) = \frac{\mu^2}{\sigma^2}\left(c - \frac{\gamma c^2}{2}\right) = g(f^{*})\cdot c\,(2-\gamma c)
$$

da cui, massimizzando rispetto a $c$: $c^{\dagger} = 1/\gamma$, coerentemente col §6.4. Per $\gamma=1$ si ritrova $c(2-c)$ del §6.2.

**Tabella di confronto** (valori in unità di $g(f^{*})$, cioè 1,00 = crescita massima del Full Kelly):

| $c$ | $\gamma=1$ (log) | $\gamma=2$ | $\gamma=4$ |
|---|---|---|---|
| $1{,}00$ | **1,000** | 0,000 | −2,000 |
| $0{,}50$ | 0,750 | **0,500** | 0,000 |
| $0{,}25$ | 0,438 | 0,375 | **0,250** |
| $0{,}10$ | 0,190 | 0,180 | 0,160 |

> [!important] Come leggere la tabella
> Il valore in grassetto di ogni colonna è l'ottimo per quel $\gamma$. Due letture:
> - Per $\gamma=2$ il Full Kelly ha certo-equivalente **esattamente zero**: un decisore moderatamente avverso al rischio è indifferente tra giocare a Full Kelly e non giocare affatto. Per $\gamma=4$ è **negativo**: preferisce strettamente non giocare. Questo è il modo quantitativamente più pulito di dire perché nessun professionista opera a Full Kelly.
> - Le colonne si appiattiscono verso il basso: a $c=0{,}10$ i tre decisori sono quasi d'accordo. **Sotto-scommettere è robusto rispetto all'ignoranza sulle proprie preferenze**, sovra-scommettere no. È lo stesso motivo, in veste diversa, per cui sotto-scommettere è robusto rispetto all'errore di stima dell'edge (§5.4).

> [!tip] Perché serve nella tesi
> È la metrica primaria corretta per confrontare gli agenti A–F. Senza di essa, un agente che cresce meno ma con metà volatilità non è confrontabile con uno più aggressivo, e la domanda "chi ha vinto?" resta ambigua o, peggio, viene risolta implicitamente scegliendo la metrica dopo aver visto i risultati. **$\gamma$ va dichiarato e fissato prima degli esperimenti**, e i risultati vanno riportati per almeno due o tre valori di $\gamma$ come analisi di sensibilità.

### 6.6 Letteratura di riferimento

- **Kelly, J. L. (1956)**, *A New Interpretation of Information Rate*, Bell System Technical Journal, 35(4), 917–926. — il paper fondativo.
- **Breiman, L. (1961)**, *Optimal Gambling Systems for Favorable Games*, Proc. 4th Berkeley Symposium on Mathematical Statistics and Probability, vol. 1, 65–78. — dimostrazione rigorosa dell'ottimalità asintotica.
- **Thorp, E. O. (1969)**, *Optimal Gambling Systems for Favorable Games*, Review of the International Statistical Institute, 37(3), 273–293. — prima applicazione sistematica del criterio a blackjack e mercati finanziari.
- **Thorp, E. O. (2006/2008)**, *The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market*, in *Handbook of Asset and Liability Management*, vol. 1, North-Holland. — rassegna divulgativa/tecnica molto citata.
- **MacLean, L. C., Ziemba, W. T., Blazenko, G. (1992)**, *Growth versus Security in Dynamic Investment Analysis*, Management Science, 38(11), 1562–1585. — introduce formalmente il trade-off "growth vs. security" e le formule del Kelly frazionario qui riportate.
- **MacLean, L. C., Thorp, E. O., Ziemba, W. T. (a cura di, 2011)**, *The Kelly Capital Growth Investment Criterion: Theory and Practice*, World Scientific Handbook in Financial Economics, vol. 3. — la raccolta di riferimento definitiva, include sia i paper "pro" sia le critiche (Samuelson).

---

## 7. Kelly multi-esito e scommesse simultanee

> [!danger]+ Perché questa sezione è indispensabile e non un approfondimento
> Tutto quanto precede assume **una scommessa binaria alla volta**. Il dominio applicativo non è così:
> - il mercato 1X2 ha **tre** esiti mutuamente esclusivi sulla stessa partita;
> - ogni giornata di campionato presenta **circa dieci partite contemporanee**, più i mercati Over/Under sulle stesse partite;
> - gli esiti delle diverse partite non sono indipendenti (fattore campo comune, condizioni meteo, effetti di calendario) e, soprattutto, gli errori del *modello* sono correlati fra partite perché provengono dallo stesso modello.
>
> Applicare la formula scalare $f^{*}=(bp-q)/b$ separatamente a ogni scommessa e poi sommare le puntate **non** dà il Kelly del portafoglio: dà una sovraesposizione sistematica. È un errore silenzioso, perché ogni singola puntata sembra prudente.

### 7.1 Kelly per esiti mutuamente esclusivi (mercato 1X2)

Con $m$ esiti mutuamente esclusivi di probabilità $p_i$ e quote decimali $d_i$ (payoff lordo per unità puntata), si punta la frazione $f_i \ge 0$ su ciascuno, con $\sum_i f_i \le 1$. Se si realizza l'esito $j$, il capitale si moltiplica per $1 - \sum_i f_i + f_j d_j$. Il problema diventa:

$$
\max_{f_1,\dots,f_m}\; \sum_{j=1}^m p_j \ln\!\Big(1 - \sum_{i=1}^m f_i + f_j d_j\Big)
\qquad \text{s.v. } f_i \ge 0,\; \sum_i f_i \le 1
$$

**Proprietà.** La funzione obiettivo è concava (somma di logaritmi di funzioni affini, stesso argomento del §2.3) su un insieme convesso: **l'ottimo esiste, è unico, ma in generale non ha forma chiusa**. Si risolve numericamente come programma concavo.

Due fatti utili:

- **Non è ottimale puntare su tutti gli esiti con edge positivo.** L'insieme degli esiti su cui si punta si determina con una procedura di selezione: si ordinano gli esiti per $p_i d_i$ decrescente e si includono finché una condizione di soglia resta soddisfatta. Alcuni esiti con $p_i d_i > 1$ possono restare esclusi, perché puntarci sottrae capitale a scommesse migliori sullo stesso evento.
- **Caso particolare importante.** Se le quote fossero *eque* ($\sum_i 1/d_i = 1$, vig nullo), l'ottimo sarebbe semplicemente $f_i = p_i$: si punta su ogni esito una frazione pari alla sua probabilità stimata. Con vig positivo questa soluzione non è più ottimale e la selezione diventa necessaria. Questo dà anche l'intuizione giusta: il vig non riduce soltanto il rendimento, **cambia la forma della soluzione**.

### 7.2 Scommesse simultanee su eventi diversi

Con $n$ partite nella stessa giornata, il problema si generalizza a una massimizzazione di $\mathbb{E}[\ln(\cdot)]$ sul vettore completo delle esposizioni. Il numero di scenari è però esponenziale ($3^n$ per soli mercati 1X2, cioè $\approx 59\,000$ per dieci partite), quindi in pratica si ricorre a un'approssimazione.

**Approssimazione quadratica (media-varianza).** Espandendo $\ln(1+x)$ al secondo ordine si ottiene un problema equivalente a Markowitz:

$$
\max_{\mathbf{f}}\; \mathbf{f}^{\top}\boldsymbol{\mu} - \tfrac{1}{2}\,\mathbf{f}^{\top}\boldsymbol{\Sigma}\,\mathbf{f}
\qquad\Longrightarrow\qquad
\mathbf{f}^{*} = \boldsymbol{\Sigma}^{-1}\boldsymbol{\mu}
$$

dove $\boldsymbol{\mu}$ è il vettore degli edge attesi e $\boldsymbol{\Sigma}$ la matrice di covarianza dei payoff. È l'esatta generalizzazione vettoriale di $f^{*}=\mu/\sigma^2$ del §5.2, e mostra dove sta il problema: **la soluzione dipende dall'inversa della matrice di covarianza**, cioè proprio dall'oggetto peggio stimato di tutti.

> [!important] Le tre conseguenze pratiche
> 1. **La correlazione riduce la size complessiva, e parecchio.** Con $n$ scommesse indipendenti di pari edge, l'esposizione totale ottimale cresce come $n$; con scommesse perfettamente correlate resta quella di una scommessa sola. La realtà sta in mezzo, ma molto più vicina al secondo caso di quanto suggerisca l'intuizione, perché gli errori condividono il modello che li ha generati.
> 2. **Il vincolo $\sum_i f_i \le 1$ non è la protezione che sembra.** Dieci scommesse al 5% ciascuna rispettano il vincolo di bankroll ma, se correlate, possono equivalere a una singola scommessa molto oltre il Full Kelly, cioè nella zona $f > 2f^{*}$ del §5.4 dove la crescita attesa è **negativa**.
> 3. **La frazione $c$ va applicata al vettore, non alle componenti.** Half-Kelly su un portafoglio significa $c\,\mathbf{f}^{*}$ con $\mathbf{f}^{*}$ già risolto congiuntamente, non "metà Kelly scalare su ciascuna scommessa calcolata isolatamente". Le due cose coincidono solo se le scommesse sono indipendenti.

> [!tip] Perché è la lacuna più pericolosa ai fini della tesi
> È un errore che non produce sintomi finché non produce il disastro: ogni riga di log mostra puntate prudenti, il codice contiene una funzione `kelly_criterion` corretta, e l'esposizione aggregata è nondimeno in territorio di crescita negativa. Nel benchmark di riferimento diversi agenti hanno esattamente questo profilo — implementazione formalmente corretta della formula scalare, nessuna gestione dell'esposizione congiunta.
>
> Conseguenza operativa: **le baseline A e B della tesi vanno specificate come vettoriali**, altrimenti quello che si sta misurando non è "Full Kelly vs Half-Kelly vs Structural-Hybrid" ma "tre modi diversi di sbagliare l'aggregazione". Va inoltre registrata a ogni giornata l'esposizione totale in unità di $f^{*}$ aggregato, come metrica diagnostica di prima classe.

---

## 8. Rischio di rovina (Risk of Ruin)

### 8.1 Rovina "teorica" vs rovina "pratica"

Nel modello puramente moltiplicativo con $f<1$, il capitale non può **mai** toccare esattamente zero: ogni fattore $(1-f)$ o $(1+fb)$ è strettamente positivo, quindi $X_n>0$ per ogni $n$ con probabilità 1. In questo senso, **la rovina totale in senso stretto ha probabilità zero** per qualunque frazione di Kelly (frazionaria o piena, purché $f<1$).

> [!note] Commento
> Questa è una proprietà elegante ma **da non fraintendere**: "non si può toccare esattamente zero" non significa affatto "non si può perdere praticamente tutto". Il capitale può avvicinarsi arbitrariamente a zero (drawdown del 99%, 99.9%, ecc.), il che nella pratica costituisce comunque una rovina operativa (impossibilità di continuare a operare, margin call, perdita del lavoro/reputazione, ecc.). Per questo si parla di **rovina pratica**, definita come il superamento di una soglia critica di perdita $a$, non come l'evento "capitale = 0".
</br>
La quantità rilevante in pratica è dunque quella del §5.3: $P(\text{caduta a frazione } a) = a^{2g/\sigma^2}$.

### 8.2 Dipendenza dalla frazione di Kelly usata: formula generale

Combinando i risultati dei §6.2 e §5.3, calcoliamo come cambia l'esponente $2g/\sigma^2$ al variare della frazione $c$ di Kelly utilizzata:

$$
\frac{2\,g(cf^{*})}{\sigma^2(cf^{*})} = \frac{2\,g(f^{*})\,c(2-c)}{c^2\,\sigma^2(f^{*})} = \frac{c(2-c)}{c^2}\cdot\underbrace{\frac{2g(f^{*})}{\sigma^2(f^{*})}}_{=\,1 \text{ (§5.2)}} = \frac{2-c}{c}
$$

$$
\boxed{P_c(\text{caduta a frazione } a) = a^{\,\frac{2}{c}-1}}
$$

Questa è una formula molto istruttiva: al **diminuire** di $c$ (size più prudente), l'esponente $\tfrac{2}{c}-1$ **cresce rapidamente**, e siccome $a<1$, un esponente maggiore significa una probabilità **molto più bassa**.

### 8.3 Tabella riepilogativa

| Frazione di Kelly $c$ | Crescita mantenuta $c(2-c)$ | Volatilità relativa $c$ | Esponente $\tfrac{2}{c}-1$ | $P(\text{dimezzamento del capitale})=0.5^{\,2/c-1}$ |
|---|---|---|---|---|
| $1.00$ (Full Kelly) | 100% | 100% | 1.00 | **50.0%** |
| $0.75$ | 93.75% | 75% | 1.67 | 31.5% |
| $0.50$ (Half-Kelly) | 75% | 50% | 3.00 | **12.5%** |
| $0.25$ (Quarter-Kelly) | 43.75% | 25% | 7.00 | 0.78% |

> [!caution] Validità dei valori in tabella
> Tutta la tabella è derivata **nell'approssimazione diffusiva** del §5.2: è esatta nel limite di scommesse piccole e frequenti, e solo approssimata per scommesse discrete con $f$ non piccolo — cioè proprio nel regime di Full Kelly su singoli eventi sportivi, dove $f^{*}$ può valere diversi punti percentuali. I valori vanno letti come **ordini di grandezza corretti e ordinamento affidabile**, non come cifre esatte. Nella tesi conviene verificarli per simulazione Monte Carlo sul processo discreto effettivo: è un controllo che costa dieci minuti e mette al riparo da un'obiezione legittima.

> [!important] Commento conclusivo sulla tabella
> Il confronto tra la prima e la seconda colonna è il cuore pratico di tutta la teoria del Kelly frazionario: passando da Full Kelly a Half-Kelly si perde solo un quarto della crescita attesa, ma la probabilità di vedere il capitale dimezzarsi lungo il percorso crolla dal 50% al 12.5% (un fattore 4×). Questo spiega perché, nella pratica professionale (trading, betting sportivo, blackjack), quasi nessuno opera a Full Kelly: il rapporto rischio/rendimento marginale è fortemente sfavorevole alle size più aggressive.

---

## 9. Critiche e limiti del criterio: la posizione di Samuelson

Non tutta la comunità accademica ha accolto il criterio di Kelly come "la" soluzione al problema dell'allocazione ottimale nel tempo. La critica più autorevole è quella di **Paul Samuelson**, premio Nobel per l'economia, che ha attaccato ripetutamente (1971, 1979) l'uso indiscriminato della massimizzazione della media geometrica / utilità logaritmica:

- **Samuelson, P. A. (1971)**, *The "Fallacy" of Maximizing the Geometric Mean in Long Sequences of Investing or Gambling*, Proceedings of the National Academy of Sciences, 68(10), 2493–2496.
- **Samuelson, P. A. (1979)**, *Why We Should Not Make Mean Log of Wealth Big Though Years to Act Are Long*, Journal of Banking and Finance, 3(4), 305–307 (DOI: 10.1016/0378-4266(79)90023-2).

**Argomento centrale di Samuelson:** massimizzare $\mathbb{E}[\ln X_N]$ è ottimale **solo** per un investitore la cui funzione di utilità è *esattamente* logaritmica. Per qualunque altra funzione di utilità (anche molto simile, es. CRRA con $\gamma$ leggermente diverso da 1), la strategia ottimale per l'investitore reale **diverge** da quella di Kelly, e questa divergenza **non si annulla** allungando l'orizzonte temporale $N$: è un errore comune credere che "nel lungo periodo tutte le utilità convergano al criterio di Kelly". Samuelson mostra che questo non è vero in generale: il fatto che Kelly "batta quasi certamente" ogni altra strategia in termini di ricchezza finale (Breiman) non implica che sia preferito da un investitore con una diversa funzione di utilità, perché quest'ultimo può razionalmente preferire una minore probabilità di rovina/drawdown a scapito della crescita attesa, anche su orizzonti lunghissimi.

> [!note] Commento — come conciliare le due posizioni
> La tensione Kelly–Samuelson non è in realtà una contraddizione logica, ma un cambio di enfasi: Breiman dimostra un fatto probabilistico oggettivo (il Kelly domina asintoticamente in ricchezza quasi certa); Samuelson osserva un fatto altrettanto oggettivo di teoria dell'utilità (dominare in ricchezza non implica dominare in utilità attesa per un decisore con preferenze diverse dal log). **Il Kelly frazionario (§6 e §8) è, in un certo senso, il punto di incontro pratico fra le due posizioni**: riconosce la superiorità strutturale della crescita geometrica ma introduce esplicitamente un parametro ($c$) per calibrare l'avversione al rischio individuale, spostando l'enfasi dalla "crescita pura" alla "crescita con sicurezza" (si veda esplicitamente il titolo di MacLean-Ziemba-Blazenko 1992: *Growth versus Security*).

---

## 10. Ponti verso la tesi

> Tre punti in cui la teoria di questi appunti incontra direttamente il disegno sperimentale. Da riprendere quasi verbatim nel Capitolo 1 della tesi.

### 10.1 Il floor di puntata rompe il risultato "la rovina è impossibile"

Il §8.1 stabilisce che nel modello puramente moltiplicativo con $f<1$ ogni fattore è strettamente positivo, quindi $X_n > 0$ per ogni $n$: la rovina in senso stretto ha probabilità zero.

**Questo risultato dipende in modo essenziale dalla puntata come *frazione* del capitale.** In presenza di una puntata minima assoluta $s_{\min}$ (un floor, che è un vincolo tipico di ogni ambiente di scommessa reale e simulato), la dinamica cambia natura:

$$
\text{stake}_t = \max\big(s_{\min},\; c\,f^{*}_t X_t\big)
$$

Quando il capitale scende sotto la soglia $X_t < s_{\min}/(c f^{*}_t)$, il floor diventa vincolante e la puntata cessa di essere una frazione: **il processo smette di essere moltiplicativo e diventa additivo verso il basso**. In quel regime, il Kelly frazionario degenera in staking piatto, la protezione contro la rovina svanisce e $X_n = 0$ diventa un evento a probabilità positiva, raggiungibile in un numero finito di giocate.

> [!important] Perché è il punto teoricamente più interessante per la tesi
> Il meccanismo ha una struttura precisa: **il floor diventa vincolante esattamente quando l'agente è già in difficoltà**, cioè quando avrebbe più bisogno di ridurre l'esposizione. È un vincolo pro-ciclico che agisce contro la gestione del rischio nel momento peggiore.
>
> Questo produce anche una previsione empirica **falsificabile**: la traiettoria di un agente a Kelly frazionario dovrebbe mostrare un cambio di regime identificabile — la varianza relativa dei rendimenti smette di essere costante e inizia a crescere — non appena il bankroll scende sotto la soglia critica. È esattamente il tipo di rottura strutturale che il Modulo 2 della tesi dovrebbe rilevare, ed è un caso in cui **si conosce la risposta giusta in anticipo**: ottimo per validare il rilevatore prima di applicarlo a rotture di cui non si conosce la natura.

Va inoltre notato che un vincolo di *almeno una scommessa per periodo* interagisce con il floor: insieme, rendono impossibile l'astensione, che il §3.2 identifica come la prescrizione corretta in assenza di edge. L'agente è obbligato a pagare una tassa deterministica a ogni giornata.

### 10.2 Nessuna regola di staking può creare edge

Ripreso dal §4.4, perché è il vincolo che definisce il perimetro di ciò che la tesi può dimostrare:

$$
g(p;\,p^{*},q) = D_{KL}(p^{*}\|q) - D_{KL}(p^{*}\|p)
$$

Il dimensionamento della puntata **non compare**. Un supervisore che ricalibra il rischio può ridurre la varianza del percorso, la probabilità di rovina e il drawdown; non può portare $g$ da negativo a positivo. L'ipotesi della tesi va formulata di conseguenza, e va formulata prima degli esperimenti, non dopo.

**Corollario operativo.** Il primo esperimento da fare, prima di qualunque cosa riguardi il Modulo 2 o 3, è misurare il log-loss del Modulo 1 contro il log-loss implicito nelle quote di chiusura. Se il primo è maggiore, allora $g<0$ per costruzione e ogni risultato successivo va interpretato come *riduzione della velocità di perdita*, non come profitto. Questo va scritto nell'abstract.

### 10.3 Metriche: cosa riportare e con quale $\gamma$

Dal §6.5: le strategie con $c$ diverso **non sono confrontabili** su crescita o su volatilità prese isolatamente. La metrica primaria è il tasso di crescita certo-equivalente, con $\gamma$ dichiarato e fissato prima degli esperimenti e riportato per almeno tre valori come analisi di sensibilità (es. $\gamma \in \{1, 2, 4\}$).

Dal §7.2: va registrata a ogni giornata l'**esposizione aggregata** in unità di $f^{*}$ di portafoglio. Senza questa diagnostica non è possibile distinguere un agente prudente da un agente che sembra prudente su ogni singola scommessa ed è complessivamente oltre $2f^{*}$.

---

## 11. Sintesi concettuale (checklist di studio)

- [ ] Saper scrivere il modello moltiplicativo $X_n = X_{n-1}(1+fb)$ o $X_{n-1}(1-f)$ e spiegare perché è moltiplicativo.
- [ ] Saper derivare $f^{*}=(bp-q)/b$ da zero, condizione del primo e del secondo ordine incluse.
- [ ] Saper spiegare la differenza fra massimizzare $\mathbb{E}[X_n]$ (lineare in $f$, ottimo a $f=1$, rovina certa) e massimizzare $\mathbb{E}[\ln X_n]$ (concavo, ottimo interno $f^{*}$).
- [ ] Saper enunciare (non necessariamente ridimostrare) il teorema di Breiman (1961) sull'ottimalità asintotica quasi certa.
- [ ] Saper derivare la relazione $\sigma^2(f^{*}) = 2g(f^{*})$ nel modello diffusivo e la formula del drawdown $P = a^{2g/\sigma^2}$.
- [ ] Saper calcolare $g(cf^{*}) = g(f^{*})\,c(2-c)$ e l'esponente di drawdown $2/c - 1$ per il Kelly frazionario.
- [ ] Saper argomentare **almeno tre** ragioni pratiche per usare Kelly frazionario invece di Full Kelly.
- [ ] Conoscere la critica di Samuelson e la sua logica (dominanza in ricchezza ≠ dominanza in utilità attesa).

**Aggiunte della revisione v2:**

- [ ] Saper scrivere e commentare la forma in divergenza $g = D_{KL}(p^{*}\|q) - D_{KL}(p^{*}\|p)$ e ricavarne, senza esitazione, il corollario che nessuna regola di staking crea edge (§4.4).
- [ ] Saper spiegare che $\ln 2 - H(p)$ è in nat e che la lettura "in bit" richiede $\log_2$ ovunque (§3.4).
- [ ] Saper distinguere le tre quantità chiamate $\sigma^2$ e dire quale entra in $P = a^{2g/\sigma^2}$ (§5.2).
- [ ] Saper scrivere $g_{CE}(cf^{*}) = g(f^{*})\,c(2-\gamma c)$, verificare che l'ottimo è $c^{\dagger}=1/\gamma$, e spiegare perché per $\gamma=2$ il Full Kelly ha certo-equivalente **zero** (§6.5).
- [ ] Saper impostare il problema di Kelly a $m$ esiti mutuamente esclusivi e dire perché non ha forma chiusa ma ha soluzione unica (§7.1).
- [ ] Saper spiegare perché $n$ scommesse "prudenti" e correlate possono superare $2f^{*}$ aggregato, e perché $\sum_i f_i \le 1$ non protegge (§7.2).
- [ ] Saper argomentare che il floor di puntata rompe la moltiplicatività e reintroduce la rovina a probabilità positiva, ed è un vincolo **pro-ciclico** (§10.1).
- [ ] Saper dire, in trenta secondi e senza appunti, cosa la tesi può e non può dimostrare, e perché (§10.2).
