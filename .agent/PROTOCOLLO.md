# Protocollo — file di stato e catene di chat

Da tenere nella repo come `.agent/PROTOCOLLO.md`.

## Convenzioni del progetto

I prompt contengono già le regole che valgono in ogni progetto: commenti e docstring in italiano; inglese per identificatori, messaggi delle eccezioni e nomi dei test; commit fatti solo dal programmatore, a mano.

Questa sezione serve per le convenzioni in più di un singolo progetto. È l'unica parte da adattare quando porti il protocollo altrove. Cline la legge in mappatura e ogni task la richiama. Le regole scritte qui sono scelte deliberate, non incoerenze.

Per questo progetto: nessuna convenzione aggiuntiva.

## I quattro prompt, in ordine di esecuzione

|N|File|Dove gira|Cosa fa|
|---|---|---|---|
|1|`1_mappatura_cline.md`|Cline, in VS Code|Ispeziona il codice e scrive `MAPPA.md`|
|2|`2_comprensione_codice.md`|Chat Claude|Assorbe la mappa e produce `SCHEDA.md`|
|3|`3_story_in_backlog.md`|Chat Claude|Trasforma una user story in `BACKLOG.md`|
|4|`4_esecuzione_story.md`|Chat Claude|Esegue i task di una story tramite Cline, uno alla volta|

Il prompt 1 è l'unico che si incolla a Cline. Gli altri tre sono system prompt di chat separate.

## Il principio

Ogni fase vive in una chat separata, che nasce e muore con la fase. Lo stato non sta nella conversazione: sta nei file dentro `.agent/`. Una chat nuova non ricostruisce niente — legge i file che le servono e lavora.

Nessuna chat continua un'altra chat. Se ti trovi a spiegare a Claude cosa è successo prima, vuol dire che manca un'informazione in uno dei file: va aggiunta lì, non raccontata.

L'esecuzione è una fase per story, non per task: una sola chat porta avanti i task di una story, con un controllo dopo ciascuno. Non è una chat ripresa: è la stessa fase che continua, e ogni task chiuso viene scritto subito nei file.

## I file

|File|Chi lo scrive|Cosa contiene|
|---|---|---|
|`.agent/MAPPA.md`|Cline|La mappa del codice, con marker `[V]`/`[D]`. Sovrascritta a ogni nuova mappatura.|
|`.agent/SCHEDA.md`|La chat di comprensione (prompt 2), aggiornata dalla chat di esecuzione (prompt 4)|Il modello del codice del supervisore: fatti distillati, marcati, con il report che li sostiene.|
|`.agent/BACKLOG.md`|La chat di scomposizione (prompt 3), aggiornato dalla chat di esecuzione (prompt 4)|Decisioni in vigore, story chiuse in breve, story aperte con i loro task, lo stato e l'esito di ciascuno.|
|`.agent/report/T<N>.md`|Cline, alla fine di ogni task|Il report finale del task: file toccati, esito dei criteri, valori misurati, deviazioni, comandi eseguiti.|

`MAPPA.md` è materiale grezzo: dopo che `SCHEDA.md` esiste, non serve più allegarlo a nessuna chat. `SCHEDA.md` e `BACKLOG.md` sono l'unico contesto che gira. I report servono a chiudere il task nella chat di esecuzione e restano come traccia dei `[V]` che la scheda cita.

Aggiungi `.agent/` al repository, non a `.gitignore`: il senso di questi file è sopravvivere alla chat e viaggiare col codice.

## Le due catene

### Catena A — dalla story al backlog

1. **In VS Code.** Incolli a Cline il Prompt 1. Cline ispeziona e scrive `.agent/MAPPA.md`. Chat chiusa.
    
2. **Chat nuova, Prompt 2.** Alleghi `MAPPA.md`. Se il supervisore ha domande, ti dà un blocco unico da incollare a Cline; riporti le risposte. Al massimo un round. In uscita: `SCHEDA.md`. Chat chiusa.
    
3. **Chat nuova, Prompt 3.** Alleghi `SCHEDA.md` e la user story, più `BACKLOG.md` se esiste già. In uscita: `BACKLOG.md`. Chat chiusa.
    
    Una story ha al massimo 5 task. Se ne servirebbero di più, la chat non produce il backlog e propone come dividere la story: la riscrivi in due e riparti.
    
    Quando il backlog esiste già, la chat riporta in forma breve le story chiuse e sposta in "Decisioni in vigore" le scelte che valgono oltre la story che le ha prese. Così il backlog resta corto, ma il contesto utile non si perde.
    

### Catena B — dal backlog al codice

1. **In VS Code.** Prompt 1, ma nella variante incrementale se una mappa esiste già. Salta questo passo se `SCHEDA.md` è ancora fresca (vedi sotto).
2. **Chat nuova, Prompt 2.** Solo se il passo 1 è stato fatto. Aggiorna `SCHEDA.md`.
3. **Chat nuova, Prompt 4.** Alleghi `SCHEDA.md` e `BACKLOG.md`. La chat sceglie la story ed esegue i suoi task in sequenza. Dopo ogni task ti dà due blocchi di aggiornamento: li applichi, fai il commit se vuoi, e scrivi "avanti". Si chiude a story finita o quando si ferma per un problema.

Il passo 3 si ripete, una chat nuova per volta, finché il backlog non è esaurito. Una story ha al massimo 5 task, quindi basta una chat per story.

## Checkpoint, pause e arresti

Dopo ogni task la chat di esecuzione si ferma e aspetta "avanti". È il momento in cui applichi i blocchi. Se nel frattempo hai toccato il codice a mano, lo dici invece di scrivere "avanti": quei file tornano `[D]` e il task successivo parte dalla ricognizione.

- **Pausa** — la chat ti chiede una decisione e poi prosegue: misura ⚖️ da guardare, divergenza fra Cline e la scheda, Cline fuori scope, decisione di prodotto sul task corrente, blocchi non applicati.
- **Arresto** — la chat chiude: criterio che non passa dopo due correttivi, indice git corrotto, backlog da rivedere. Il resto va in una chat nuova.

## Quando la scheda va rifatta

`SCHEDA.md` porta in fondo `Ultimo aggiornamento`, con l'elenco dei task di scrittura chiusi dopo l'ultima mappatura. Ogni blocco di chiusura lo allunga di un task; ogni mappatura lo riporta a "nessuno".

- **Fresca** (elenco vuoto) → apri direttamente la chat di esecuzione.
- **Invecchiata di poco** (da uno a quattro task) → le voci che dipendono dai file toccati sono già `[D]`, perché i blocchi di chiusura le declassano; la chat di esecuzione le fa riverificare nella ricognizione. Niente rimappatura.
- **Invecchiata molto** (più di quattro task, o modifiche strutturali) → rifai la catena: mappatura incrementale, poi il prompt 2.

Il controllo si fa all'apertura della chat di esecuzione. Dentro la chat, i task chiusi non fanno scattare la soglia: il supervisore ha visto ogni modifica. La faranno scattare per la chat successiva.

Rimappare costa; non rimappare mai costa di più. La soglia sopra è una convenzione, non una legge: se la scheda ti sembra scollata dal codice, rimappa.

## Numerazione dei report

Ogni risposta di Cline dentro una sessione è numerata `R1`, `R2`, … Nella chat di esecuzione la numerazione continua da un task all'altro. Poiché le sessioni sono separate, la scheda cita i report come `R2@2026-09-09`: report 2 della sessione di quel giorno. Senza data il riferimento è ambiguo fra sessioni diverse.

## Cosa non fare

- Non allegare il codice alle chat del supervisore. Il supervisore ragiona sulla scheda; il codice lo legge Cline.
- Non tenere due chat aperte sulla stessa fase.
- Non riprendere una chat vecchia "perché tanto ha già il contesto": il contesto che ha è invecchiato, ed è la fonte di errore più frequente.
- Non scrivere "avanti" senza aver applicato i blocchi, né dopo aver toccato il codice a mano senza dirlo.
- Non far scrivere a Cline in `.agent/`, a parte `MAPPA.md` in mappatura e `report/T<N>.md` in esecuzione.