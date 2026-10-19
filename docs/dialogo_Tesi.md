alve, ovviamente do tesi, ma in questo momento sono concentrato su questo problema per cui le passo il paper in attach; se può essere interessato dopo averlo letto bene, si faccia gentilmente risentire, cordiali saluti
 
 
Marco Roccetti
www.unibo.it/sitoweb/marco.roccetti/
www.unibo.it/sitoweb/marco.roccetti/en
------------
Privacy notice: The information and files in this message are confidential and are intended solely for the use of the addressed recipient. Any unauthorized use, copying, disclosure, or distribution, in whole or in part, is strictly prohibited.
Federico Malservigi - federico.malservigi@studio.unibo.it<federico.malservigi@studio.unibo.it>
 
Marco Roccetti
Gentile professore,
 
ho letto il paper su KellyBench e lo trovo un tema molto stimolante, soprattutto per i legami con la valutazione di agenti LLM in ambienti non-stazionari — un argomento su cui vorrei approfondire anche in vista di una magistrale in AI.
 
Sarei molto interessato a sviluppare una tesi su questo tema. Se ritiene che ci possano essere margini per collaborare, sono disponibile per un appuntamento nei modi e nei tempi che preferisce.
 
Cordiali saluti,
Federico Malservigi
Marco Roccetti
 
Salve sto aspettando risposta anche da un altro suo collega cui avevo proposto tma analogo, voglio capire se lui è o meno interessato poi le faccio sapere saluti
 
 
Marco Roccetti
www.unibo.it/sitoweb/marco.roccetti/
www.unibo.it/sitoweb/marco.roccetti/en
------------
Privacy notice: The information and files in this message are confidential and are intended solely for the use of the addressed recipient. Any unauthorized use, copying, disclosure, or distribution, in whole or in part, is strictly prohibited.
Marco Roccetti
 
Marco Roccetti
Dunque se vuole provare a capire in che direzione modellistico sperimentale vorrei andare per una tesi del genere, provi a leggere questo scambio con amico -collega cosi' capisce (da tenere riservato), poi mi dice se ha capito e se le interessa
 
Saluti
-----
"Scusami PG, non dico che stavo per scrivere uno dei miei paper di protesta (anche perché il paper di Taylor è ancora non peer reviewed) ma ci stavo pensando. Il paper in sintesi dice:
 
1. Hanno preso l'intera stagione 2023-2024 della Premier League inglese e l'hanno trasformata in un simulatore. L'IA viene messa in una stanza virtuale con un budget (es. £100.000).Deve vivere la stagione giorno per giorno, come se fosse un vero scommettitore professionista
 
2. L'ambiente fornisce all'IA una montagna di dati: Il Passato: Tutti i risultati dei match dal 1993 a oggi.Il Presente: Statistiche dettagliate sui giocatori, formazioni, gol attesi, infortuni. Il Mercato: Le quote offerte dai bookmaker in tempo reale.
 
3. La Sfida: Non basta che l'IA dica: "Secondo me vince il City". Deve decidere quanti soldi puntare su quella previsione. Se punta troppo e sbaglia, va in bancarotta (Ruin).Se punta troppo poco, non guadagna nulla.
 
Per vincere, deve usare il Criterio di Kelly: una formula matematica che calcola la puntata perfetta bilanciando il vantaggio (edge) e il rischio.
 
4. Le Trappole.
La Non-Stazionarietà: I ricercatori hanno inserito delle trappole per vedere se l'IA è intelligente o se ripete solo a memoria: Le squadre neopromosse (Luton, Burnley): Squadre di cui l'IA non ha dati recenti nel database storico. Se l'IA non capisce che il mondo è cambiato, fa calcoli sbagliati.
 
L'evoluzione in corso: Se una strategia smette di funzionare a metà stagione, l'IA è capace di fermarsi e ricalibrare o continua a sbattere la testa contro il muro?
 
In sintesi: Cosa è successo nell'esperimento? Hanno testato i modelli più potenti (GPT-4, Claude, Gemini) e il risultato è stato un disastro quasi totale: hanno perso quasi tutti i soldi.
 
In più i ricercatori evidenziano: Le IA parlavano bene (Userò il criterio di Kelly), ma poi agivano male (puntavano cifre a caso o dimenticavano di aggiornare i calcoli). Non appena incontravano una situazione nuova (le neopromosse), i loro modelli esplodevano perché non sapevano gestire la non-stazionarietà.
 
Fin qua il paper. 
 
Ora parto io.
 
A. C'è la solita ingiustizia Epistemica (Rigid-Kelly Trap). Affermare che l'IA fallisce perché non batte il mercato usando Kelly rigido è un bias metodologico.
 
La trappola: è che Kelly presuppone che tu conosca la vera probabilità. Ma in un sistema non-stazionario ed eteroschedastico (dove la varianza cresce con la media, tipico dei mercati sportivi), la stima della probabilità è intrinsecamente rumorosa e dunque i ricercatori hanno cratoil tipico paradosso di questi esperimenti: Se imponi il Full Kelly a un'entità che non ha strumenti per misurare la propria ignoranza statistica, la stai condannando alla rovina. Gli umani infatti usano il Fractional Kelly che sono euristiche derivate dal Kelly proprio perché riconoscono di non avere una conoscenza perfetta. Negare all'IA questo grado di libertà (o non dotarla di un modulo di umiltà algoritmica) è l'ingiustizia epistemica
 
Se ne esce in due modi
 
B La Soluzione Standard (Data-Driven): "Dateci i dati del Betting": questa è la risposta classica della Silicon Valley: "Serve più data-learning". Dando all'IA i dati storici delle quote (il mercato), l'IA potrebbe imparare non solo a prevedere il calcio, ma a prevedere l'errore del mercato. Imparerebbe la distribuzione della stupidità dei bookmaker. Tuttavia, attento, resterebbe comunque un approccio chiuso: se il mercato cambia improvvisamente (nuova regolamentazione, algoritmi dei bookmaker più raffinati), l'IA si schianterebbe di nuovo.
 
C La mia Soluzione (Structural-Hybrid): "L'Algoritmo in the Loop". Qui è dove superiamo il paper. Io propongo un Agente di Secondo Livello. Non un'IA che scommette e basta, ma un sistema gerarchico: Modulo 1 (Il Lavoratore): Fa le previsioni (modelli classici/LLM).Modulo 2 (Il Supervisore - Il mio framework):
 
Monitora i residui tramite ANOVA. Quando rileva che l'eteroschedasticità sta aumentando (ovvero che la media degli errori cresce e la varianza esplode), suona l'allarme e scatta il Modulo 3 (Il Ricalibratore): Usa Blinder-Oaxaca per scomporre il fallimento. È un errore del dato  (es. infortunio improvviso). Allora riduco un po' lo stake. È un errore strutturale  (es. il mercato è cambiato o la squadra ha cambiato anima). Allora ricalibro il rischio quasi a zero o cambio modello.
 
Sostanziamnete uso due modelli classi ci Anova e Blinder_Oaxaca per rivcalibrare il rischio quando varianza aumenta e per capire quanto di strutturale o meno ci sia nel cambio della medesima
 
Lanciamo la sfida. Un agente così configurato vincerebbe perché diventa  consapevole dei propri limiti: Non usa Kelly come un dogma, ma come una variabile dipendente dalla stabilità del sistema. Distingue il rumore dalla struttura: Grazie alla scomposizione di Oaxaca, capisce se il mondo è solo sporco o se è proprio diverso".
 
Riassunto della soluzione più chiaro:
Structural-Hybrid propongo un sistema gerarchico dove l'IA che scommette è solo il braccio, il cervello è un Agente di Secondo Livello che:
Monitora i residui tramite ANOVA. Se l'eteroschedasticità aumenta (varianza che cresce con la media), scatta l'allarme.
Usa la Decomposizione di Blinder-Oaxaca per separare l'errore: è dovuto ai dati (infortunio, caso) o alla struttura (cambio di regime del mercato)?
Ricalibra lo stake di conseguenza: se il fallimento è strutturale, il rischio va a zero finché il modello non viene ri-parametrizzato.
Mentre Taylor dice 'l'IA non è capace', io dico che l'esperimento è mal disegnato: manca il modulo di ricalibrazione del rischio strutturale. Un agente con ANOVA e Oaxaca in the loop non solo non fallisce, ma batte il mercato perché tratta la stabilità del sistema come una variabile endogena, non come un dogma.
Scommettiamo? Un sistema così darebbe del filo da torcere anche ai sindacati dei professionisti del betting. Che ne pensi?"
 
-----
 
Marco Roccetti
www.unibo.it/sitoweb/marco.roccetti/
www.unibo.it/sitoweb/marco.roccetti/en
------------
Privacy notice: The information and files in this message are confidential and are intended solely for the use of the addressed recipient. Any unauthorized use, copying, disclosure, or distribution, in whole or in part, is strictly prohibited.
Federico Malservigi - federico.malservigi@studio.unibo.it<federico.malservigi@studio.unibo.it>
 
Marco Roccetti
Salve,
 
Ho apprezzato molto la possibilità di leggere il ragionamento dietro la proposta.
 
Ho capito la critica al paper: imporre il Kelly rigido a un sistema che non ha strumenti per misurare la propria incertezza statistica è un bias metodologico, non un limite dell'AI in sé. La parte sul sistema gerarchico con i due moduli di supervisione è quella che ho trovato più stimolante, anche se sono onesto: alcune parti tecniche le ho capite solo in parte e avrei bisogno di approfondirle.
 
Sono comunque molto interessato a lavorare su questo tema e disposto a investirci. Se ritiene che ci siano i margini per svilupparlo come tesi, sarei felice di fissare un appuntamento per capire come impostare il lavoro (anche uno scambio di mail).
 
Cordiali Saluti,
Federico Malservigi
Marco Roccetti
 
Sarebbe un'ottima tesi se vuole mi chiami anche da ora che impostiamo 3920271318
 
 
Marco Roccetti
www.unibo.it/sitoweb/marco.roccetti/
www.unibo.it/sitoweb/marco.roccetti/en
------------
Privacy notice: The information and files in this message are confidential and are intended solely for the use of the addressed recipient. Any unauthorized use, copying, disclosure, or distribution, in whole or in part, is strictly prohibited.
Marco Roccetti
 
Marco Roccetti
Come promesso, Le passo in attach 2/3 miei paper recenti in cui uso e/o propongo tecniche varie per analisi della varianza (variance partitioning). Sempre tenendo a riferimento che il punto di partenza è ANOVA di Fisher, magari i miei lavori anche se applicati in altro contesto (medico farmacologico) le possono cmq dare spunti, saluti