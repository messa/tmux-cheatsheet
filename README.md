# tmux cheatsheet

Poznámky a tahák k tmuxu (psáno pro tmux 3.x).

## Obsah

- [Na co je to dobré](#na-co-je-to-dobré)
- [Méně známé triky](#méně-známé-triky)
- [Slovníček pojmů](#slovníček-pojmů)
- [Jak se čtou zkratky](#jak-se-čtou-zkratky)
- [Sessions](#sessions)
- [Windows](#windows)
- [Panes](#panes)
- [Výpisy](#výpisy)
- [Automatizace a skriptování](#automatizace-a-skriptování)
- [Copy mode a schránka](#copy-mode-a-schránka)
- [Ostatní užitečné](#ostatní-užitečné)
- [Konfigurace](#konfigurace)
- [tmux a Claude Code](#tmux-a-claude-code)
- [Pluginy](#pluginy)

---

## Na co je to dobré

Hlavní důvod, proč se tmux učit, je jeden:

- **Práce přežije spojení.** Pustíš na serveru migraci, build nebo
  `apt upgrade`, spadne ti SSH — a proces běží dál. Vrátíš se přes `tmux a`.
  Idiom hned po přihlášení: `tmux a || tmux` (připoj se, případně založ novou
  session).

Zbytek jsou věci, které dostaneš, když už ho máš:

- **Session na projekt.** Místo tabů terminálu, které zmizí s jeho zavřením,
  `tmux a -t projekt` — okna s nastavenými adresáři a rozdělanou prací přežijí
  restart terminálu, odhlášení i pád okenního správce.
- **Panes na sledování.** Editor v jednom panu, testy ve druhém, `tail -f`
  logu ve třetím — všechno viditelné naráz.
- **Dlouho běžící proces bez systemd.** `tmux new -d -s tunel 'ssh -L …'` —
  nejrychlejší cesta k „běž na pozadí a můžu se na to kdykoli podívat“.
- **Skriptování zvenčí.** `tmux send-keys -t prace 'make test' Enter` — jeden
  skript nastartuje celé prostředí nebo pošle vstup běžící aplikaci. Na tomhle
  stojí tmuxinator i [agent teams Claude Code](#agent-teams-ve-split-panes).
- **Sdílení session.** Dva lidé na jednom stroji, oba vidí totéž — párové
  programování bez screensharingu. Viz také
  [sledování bez možnosti zásahu](#sledování-bez-možnosti-zásahu).
- **Scrollback a hledání.** `prefix [` a hledáš v tisících řádků výstupu,
  nezávisle na schopnostech terminálu — funguje i v holém tty.
- **Splity a taby tam, kde terminál žádné neumí.** Linuxová konzole, serial
  console, cizí stroj s hloupým terminálem.

Vedlejší efekt: čím víc věcí žije v tmuxu, tím míň záleží na tom, jaký
terminálový emulátor zrovna používáš — zkratky, splity i sessions si neseš
s sebou.

---

## Méně známé triky

Všechno níže je v holém tmuxu bez pluginů (popupy a `-e` potřebují
tmux ≥ 3.2). Pojmy vysvětluje [Slovníček](#slovníček-pojmů).

### Pane jako objekt: číst, logovat, restartovat

Na pane se dá zvenčí nejen psát (`send-keys`, viz
[Ostatní užitečné](#ostatní-užitečné)), ale i číst z něj a řídit ho:

```bash
tmux capture-pane -p -t prace:0.1        # vypíše, co je v panu vidět
tmux capture-pane -p -S - -t prace:0.1   # totéž včetně celého scrollbacku

tmux pipe-pane -o -t prace:0.1 'cat >>~/pane.log'   # od teď logovat do souboru
tmux pipe-pane -t prace:0.1                          # vypnout logování

tmux respawn-pane -k -t prace:0.1 'npm run dev'      # restart příkazu v panu
```

`capture-pane` znamená, že můžeš grepovat výstup procesu, který si nikam
neloguje — a je to i způsob, jak do terminálu „vidí“ AI agenti. `pipe-pane`
zachrání situaci, kdy si v půlce hodinového buildu vzpomeneš, že výstup chceš
uložit. `respawn-pane -k` vymění zamrzlý proces bez rozbití layoutu.

### `wait-for`: semafor zadarmo

```bash
# skript nebo pane A: čekej na signál
tmux wait-for build-hotov

# pane B: až doběhne build, signalizuj
make build; tmux wait-for -S build-hotov
```

Blokuje, dokud nepřijde `-S` se stejným jménem kanálu. Deterministická
synchronizace mezi panes, okny a skripty — tam, kde by jinak byl `sleep`
a hádání. `-L`/`-U` navíc umí zámek (lock/unlock).

### Popup: plovoucí okno nad layoutem

```tmux
bind g display-popup -E -w 80% -h 80% -d "#{pane_current_path}" 'lazygit'
bind N display-popup -E 'vim ~/poznamky.md'
```

`display-popup` otevře program v okně plovoucím nad panes — layout nechá být,
`-E` popup zavře, jakmile program skončí. Ideální na git UI, poznámky nebo
rychlou kalkulačku. Příbuzný `display-menu` staví vlastní kontextová menu.

### Psát do všech panes naráz

```tmux
setw synchronize-panes on    # a potom zase off
```

Co napíšeš, jde do všech panes v okně současně. Čtyři panes, v každém SSH na
jiný server — jednorázový zásah na čtyřech strojích bez Ansiblu. Hodí se jako
toggle: `bind S setw synchronize-panes` (bool volba bez hodnoty se přepne).

### Upozornění, že příkaz doběhl

```tmux
setw monitor-silence 30      # ohlaš, když je okno 30 s zticha
setw monitor-activity on     # ohlaš jakýkoli výstup v okně na pozadí
```

Okno se ve status baru označí `~` (ticho) resp. `#` (aktivita). Na „řekni mi,
až build skončí“ je `monitor-silence` chytřejší — zajímá tě, kdy výstup
*přestal*, ne že nějaký je. `set -g visual-silence on` k tomu ukáže i zprávu.

### Víc serverů vedle sebe

```bash
tmux -L agenti new -d -s x    # oddělený server s vlastním socketem
tmux -L agenti ls             # …vlastní sessions, vlastní konfigurace
```

Server je vázaný na socket; `-L jmeno` založí další socket (a tedy server)
vedle defaultního. Izolovaný svět — `kill-server` v něm nesáhne na tvoje
běžné sessions. Hodí se na experimenty nebo pro automatizaci, která si nemá
špinit tvůj pracovní server.

`-S /cesta/k/socketu` určí socket plnou cestou — tudy vede i sdílení tmuxu
mezi dvěma OS uživateli (socket na společně přístupném místě + práva, typicky
přes společnou skupinu).

### Sledování bez možnosti zásahu

```bash
tmux attach -r -t prezentace           # read-only klient
tmux attach -f active-pane -t work     # klient s vlastním aktivním panem
```

Read-only klient všechno vidí, ale nic nenapíše (funguje mu jen detach) —
dobré na prezentace a „koukej mi přes rameno“. `-r` je zkratka za
`-f read-only,ignore-size`, takže zároveň nezmenší okno ostatním.

`active-pane` dá klientovi vlastní kurzor: dva lidé v jednom okně, každý
v jiném panu. Doplněk ke
[grouped sessions](#víc-klientů-každý-na-jiném-okně-grouped-sessions), které
řeší totéž o úroveň výš — vlastní aktivní *okno*.

### Vnořený tmux: vypnout ten vnější jednou klávesou

Lokální tmux + tmux na serveru = prefix se pere a všechno mačkáš dvakrát.
Nabinduj si vypínač celého vnějšího tmuxu:

```tmux
bind -T root F12 set prefix None \; set key-table off \; display "tmux OFF"
bind -T off  F12 set -u prefix \; set -u key-table \; display "tmux ON"
```

`F12` přepne vnější tmux do prázdné key table `off` — od té chvíle jde každá
klávesa včetně prefixu dovnitř, do vnořeného tmuxu. Druhé `F12` ho probudí.
Jméno tabulky `off` není nic magického, je vymyšlené.

### Status bar ví, že jsi zmáčkl prefix

```tmux
set -g status-right "#{?client_prefix,#[reverse] PREFIX #[default],}%H:%M"
```

`#{?client_prefix,…,…}` je podmínka (viz [Vlastní formát](#vlastní-formát--f))
— proměnná je 1, dokud tmux čeká na druhou klávesu zkratky. Nečekaně užitečné
při učení zkratek: vidíš, že prefix „drží“.

### Drobnosti

- `tmux new -s x -e FOO=bar` — env proměnná jen pro tuhle session (dostanou ji
  nové panes). Dobré na `AWS_PROFILE` a podobné bez špinění globálního
  prostředí.
- `tmux new -A -s x` — připoj se, a když session neexistuje, založ ji. Skvělé
  interaktivně, ale ve skriptu bez terminálu spadne na `open terminal failed`
  (z `new` se stane attach). Tam patří
  `tmux has-session -t x 2>/dev/null || tmux new -d -s x`.

---

## Slovníček pojmů

Jak to do sebe zapadá:

```text
     ┌────────────┐            ┌────────────┐
     │  client A  │            │  client B  │
     │ (terminál) │            │ (SSH)      │
     └─────┬──────┘            └─────┬──────┘
           │ attach / detach         │
           ▼                         ▼
┌ server (proces na pozadí) ─────────────────────────────┐
│                                                        │
│ ┌ session: web ──────────────────┐ ┌ session: api ───┐ │
│ │                                │ │                 │ │
│ │ ┌ window 0 ─┐ ┌ window 1 ────┐ │ │ ┌ window 0 ───┐ │ │
│ │ │           │ │      │ pane  │ │ │ │             │ │ │
│ │ │   pane    │ │ pane ├───────┤ │ │ │    pane     │ │ │
│ │ │           │ │      │ pane  │ │ │ │             │ │ │
│ │ └───────────┘ └──────┴───────┘ │ │ └─────────────┘ │ │
│ └────────────────────────────────┘ └─────────────────┘ │
└────────────────────────────────────────────────────────┘
```

Každý pane je samostatný terminál, ve kterém běží (typicky) shell. Oba klienti
se také mohou připojit ke stejné session naráz — viz
[grouped sessions](#víc-klientů-každý-na-jiném-okně-grouped-sessions).

### server

Proces, který běží na pozadí a drží všechny sessions, windows a panes. Startuje se
automaticky při prvním `tmux` a běží dál, i když zavřeš terminál. Proto ti věci
v tmuxu přežijí zavření okna terminálu nebo odpojení SSH.

Server je **per OS uživatel** — každý účet má svůj, komunikuje se s ním přes
socket v `/tmp/tmux-<UID>/` (adresář má práva `700`; jinam ho přesune
`$TMUX_TMPDIR`). Sessions jiných uživatelů proto nevidíš a `sudo tmux` mluví
s úplně jiným serverem. Přesněji je server vázaný na *socket* — jeden uživatel
jich může mít víc, viz [Víc serverů vedle sebe](#víc-serverů-vedle-sebe).

Když skončí poslední session, server se ukončí.

### client

Tvůj terminál připojený k serveru. K jedné session může být připojeno víc klientů
najednou (typicky když sdílíš session s kolegou nebo ji máš otevřenou na dvou
monitorech).

### session

Nejvyšší úroveň skupiny — jedna "pracovní plocha". Obsahuje jedno nebo víc oken
(windows). Session má jméno (`0`, `1`, … nebo vlastní, např. `web`, `api`).

Typicky se dělá jedna session na projekt. Session žije na serveru nezávisle na
tvém terminálu — od toho je celý tmux: **detach** (odpojíš se, session běží dál)
a **attach** (znovu se připojíš).

### session group

Několik sessions sdílejících stejnou sadu oken, ale každá s vlastním aktivním
oknem. Vzniká přes `new-session -t`. Používá se, když chceš mít v každém
terminálu otevřené jiné okno téhož projektu — viz
[Víc klientů, každý na jiném okně](#víc-klientů-každý-na-jiném-okně-grouped-sessions).

### window

Okno uvnitř session — obdoba záložky (tabu) v terminálu. V daný okamžik vidíš
v session právě jedno window. Seznam oken je ve status baru dole.

Každé window má číslo (index) a jméno. Jméno se defaultně mění podle běžícího
programu, dá se přejmenovat.

### pane

Rozdělená část okna — jeden konkrétní terminál s jedním shellem. Window se dá
rozřezat na libovolný počet panes horizontálně i vertikálně, všechny vidíš
najednou vedle sebe.

Když se v panu ukončí shell (`exit`, Ctrl-D), pane zmizí. Když zmizí poslední
pane v okně, zmizí okno. Když zmizí poslední okno, skončí session.

**Hierarchie:** `server → session → window → pane`

### prefix

Klávesová zkratka, kterou uvedeš každý tmux příkaz, aby tmux poznal, že klávesa
patří jemu a ne programu uvnitř. Defaultně **`Ctrl-b`**.

Zápis `prefix c` znamená: stiskni `Ctrl-b`, pusť, pak stiskni `c`.

Hodně lidí si prefix mění na `Ctrl-a` (dědictví ze screenu, na klávesnici blíž),
viz [Konfigurace](#konfigurace).

### status bar

Řádek dole. Vlevo jméno session, uprostřed seznam oken, vpravo hostname a čas.
Aktuální okno je označené `*`, předchozí `-`.

### detach / attach

**Detach** = odpojení klienta od session, všechno uvnitř běží dál na serveru.
**Attach** = opětovné připojení. Toto je hlavní důvod, proč tmux používat na
vzdálených serverech — spadne ti SSH, ale procesy běží dál.

### copy mode

Režim, ve kterém můžeš scrollovat historií výstupu, hledat v ní a kopírovat text.
Dokud jsi v copy mode, klávesy nejdou do shellu. Zapíná se `prefix [`, ven
`q` (nebo `Escape`).

### layout

Předdefinované rozvržení panes v okně (`even-horizontal`, `main-vertical`, …).
Přepíná se `prefix Space`.

### command mode

Řádek pro psaní tmux příkazů přímo (jako `:` ve Vimu). Otevře se `prefix :`,
napíšeš např. `new-window -n logs`. Všechno, co jde přes klávesovou zkratku, jde
i tudy — a navíc spousta věcí, na které zkratka není.

### key table

Sada zkratek platná v daném režimu. Normálně se používá tabulka `prefix`
(zkratky po stisku prefixu), tabulka `root` drží klávesy fungující **bez**
prefixu a v copy mode platí `copy-mode-vi` / `copy-mode`. Uvidíš to ve výpisu
`tmux list-keys`.

---

## Jak se čtou zkratky

- `prefix c` = stiskni `Ctrl-b`, pusť, pak `c`
- `Ctrl-b c` = totéž
- `tmux ls` = příkaz do shellu (mimo tmux i uvnitř)
- `:new-window` = tmux příkaz zadaný přes `prefix :`

Skoro každá zkratka má svůj příkazový ekvivalent — zkratka `prefix c` volá
příkaz `new-window`.

---

## Sessions

Session je nejvyšší úroveň skupiny — jedna "pracovní plocha". Obsahuje jedno nebo víc oken
(windows).

### Ze shellu

| Příkaz | Co dělá |
| --- | --- |
| `tmux` | Nová session (jméno `0`, `1`, …) |
| `tmux new -s jmeno` | Nová session s daným jménem |
| `tmux new -s jmeno -d` | Nová session na pozadí (nepřipojí se) |
| `tmux ls` | Seznam sessions |
| `tmux a` | Připojí se k poslední session |
| `tmux a -t jmeno` | Připojí se ke konkrétní session |
| `tmux a -d -t jmeno` | Připojí se a odpojí ostatní klienty |
| `tmux kill-session -t jmeno` | Zabije session |
| `tmux kill-server` | Zabije úplně všechno |

`tmux a` je zkratka za `attach-session`, `tmux new` za `new-session`.

### Zevnitř tmuxu

| Zkratka | Co dělá |
| --- | --- |
| `prefix d` | Detach (odpojí se, session běží dál) |
| `prefix s` | Interaktivní seznam sessions (šipky + Enter) |
| `prefix $` | Přejmenuje session |
| `prefix (` | Předchozí session |
| `prefix )` | Další session |
| `prefix L` | Přepne na poslední (naposledy použitou) session |
| `prefix D` | Seznam připojených klientů (dají se odpojit) |
| `:new-session -s jmeno` | Nová session bez opuštění tmuxu |
| `:kill-session` | Zabije aktuální session |

### Víc klientů, každý na jiném okně (grouped sessions)

Když se dva klienti připojí ke **stejné** session, jsou zrcadlem — sdílí current
window, takže přepnutí okna v jednom přepne i druhého. To se občas hodí (párové
programování), ale často ne.

Řešení je **grouped session** — `new-session -t`:

```bash
tmux new-session -t work -s work-2   # work-2 sdílí okna s work, ale má vlastní current window

# terminál 1
tmux attach -t work
# terminál 2
tmux attach -t work-2
```

Sessions ve skupině sdílí seznam oken, ale každá má vlastní aktivní okno. V
`tmux ls` jsou označené `(group 0)`.

- Nové okno vytvořené v kterékoli session skupiny se objeví ve všech.
- Zavření okna ho zavře pro celou skupinu.
- Zabití jedné session ze skupiny okna nezruší — žijí dál v ostatních.

Pokud nechceš sdílet celou sadu oken, ale jen některá, naskládej je do
samostatné session ručně přes `:link-window -t jina-session`.

> **Past na velikost okna.** tmux defaultně zmenší okno na velikost nejmenšího
> připojeného klienta — na dvou různě velkých terminálech pak dostaneš kolem
> okna rámeček z teček. Řešení:
>
> ```tmux
> setw -g aggressive-resize on   # řídí se nejmenším klientem, který okno OPRAVDU zobrazuje
> set -g window-size largest     # hrubší varianta: vždy podle největšího klienta
> ```
>
> Pro grouped sessions je správná volba `aggressive-resize`.

---

## Windows

Window je okno uvnitř session — obdoba záložky (tabu) v terminálu.

| Zkratka | Co dělá |
| --- | --- |
| `prefix c` | Nové okno |
| `prefix ,` | Přejmenuje okno |
| `prefix &` | Zavře okno (ptá se na potvrzení) |
| `prefix 0`–`9` | Přepne na okno podle čísla |
| `prefix n` | Další okno |
| `prefix p` | Předchozí okno |
| `prefix l` | Poslední (naposledy použité) okno |
| `prefix w` | Interaktivní seznam oken napříč sessions |
| `prefix f` | Najde okno podle textu |
| `prefix .` | Změní číslo okna (přesune ho v pořadí) |

Užitečné příkazy:

```
:new-window -n logs          # nové okno s daným jménem
:new-window -c ~/projekt     # nové okno se startovním adresářem
:swap-window -t 2            # prohodí aktuální okno s oknem 2
:move-window -t 1            # přesune okno na pozici 1
:movew -r                    # přečísluje okna od nuly (zacelí díry)
```

---

## Panes

Pane je rozdělená část okna — jeden konkrétní terminál s jedním shellem.

### Vytváření a rušení

| Zkratka | Příkaz | Co dělá |
| --- | --- | --- |
| `prefix %` | `split-window -h` | Rozdělí pane na levý a pravý |
| `prefix "` | `split-window -v` | Rozdělí pane na horní a dolní |
| `prefix x` | `kill-pane` | Zavře pane (ptá se) |
| `prefix !` | `break-pane` | Vytáhne pane do samostatného okna |
| `prefix z` | `resize-pane -Z` | Zoom — zvětší pane na celé okno / vrátí zpět |

> **Pozor na terminologii.** tmux nazývá split podle *směru dělící čáry z pohledu
> parametru*, ne podle toho, jak to vypadá. `-h` (horizontal split, `%`) dá panes
> **vedle sebe** s **svislou** dělící čarou. `-v` (vertical split, `"`) dá panes
> **pod sebe**. Je to opačně, než většina lidí čeká.
>
> Mnemotechnika podle tvaru znaku funguje spolehlivě: `%` obsahuje svislou čáru →
> panes vedle sebe. `"` má dvě čárky vedle sebe nahoře → dělící čára vodorovná,
> panes pod sebou.

Split se startovním adresářem aktuálního panu:

```
:split-window -h -c "#{pane_current_path}"
:split-window -v -c "#{pane_current_path}"
```

### Pohyb mezi panes

| Zkratka | Co dělá |
| --- | --- |
| `prefix šipka` | Přepne na pane daným směrem |
| `prefix o` | Cyklicky další pane |
| `prefix ;` | Poslední (naposledy použitý) pane |
| `prefix q` | Zobrazí čísla panes; stiskem čísla přepneš |
| `prefix {` | Prohodí pane s předchozím |
| `prefix }` | Prohodí pane s dalším |
| `prefix Ctrl-o` | Zrotuje panes v okně |
| `prefix m` | Označí pane (marked pane) |
| `prefix M` | Zruší označení |

Označený pane (`prefix m`) slouží jako výchozí zdroj pro `join-pane`,
`swap-pane` a `move-pane`. Typické použití — přesun panu z jiného okna k sobě:
označíš ho `prefix m`, přepneš se kam chceš a dáš `:join-pane`.

### Velikost a rozvržení

| Zkratka | Co dělá |
| --- | --- |
| `prefix Ctrl-šipka` | Změní velikost panu po 1 buňce |
| `prefix Alt-šipka` | Změní velikost panu po 5 buňkách |
| `prefix Space` | Přepne na další layout |
| `prefix Alt-1`–`Alt-5` | Konkrétní layout (even-horizontal … tiled) |

```
:resize-pane -D 10           # zvětší dolů o 10 řádků
:resize-pane -Z              # zoom (totéž co prefix z)
:select-layout tiled
```

---

## Výpisy

| Zkráceně | Plný název | Co vypíše |
| --- | --- | --- |
| `tmux ls` | `tmux list-sessions` | Sessions |
| `tmux lsw` | `tmux list-windows` | Okna aktuální session |
| `tmux lsw -a` | `tmux list-windows -a` | Okna **všech** sessions |
| `tmux lsp` | `tmux list-panes` | Panes aktuálního okna |
| `tmux lsp -s` | `tmux list-panes -s` | Panes celé session |
| `tmux lsp -a` | `tmux list-panes -a` | Panes **všech** sessions |

Díky `-a` není potřeba cyklit přes sessions — jeden příkaz vypíše celý server.

### Vlastní formát (`-F`)

Přehled všech panes s cestou, ve které stojí jejich shell:

```bash
tmux lsp -a -F '#{p22:#{session_name}:#{window_index}.#{pane_index}} #{p28:window_name} #{s|#{HOME}|~|:pane_current_path}'
```

```text
web:1.1                nvim                         ~/projekt
web:2.1                bash                         ~/projekt/docs
api:1.1                pytest                       ~/code/api
api:1.2                Deploy staging               ~/code/api/infra
```

Tenhle příkaz je v repu jako [`tmux_list_panes.sh`](tmux_list_panes.sh).

Co dělají jednotlivé kousky formátu:

| Zápis | Význam |
| --- | --- |
| `#{p22:…}` | Zarovná na 22 znaků (doplní mezery zprava) — dělá sloupce |
| `#{s\|vzor\|náhrada\|:…}` | Nahradí regexem — tady `$HOME` za `~` |
| `#{pane_current_path}` | Pracovní adresář panu |
| `#{window_name}` | Jméno okna (v Claude Code sedí na rozdělanou práci) |

Formátovací proměnné se dají vnořovat (`#{p22:#{session_name}:…}`), celý seznam
dá `tmux display-message -a`.

### Filtrování (`-f`)

Ve kterých oknech mám otevřený konkrétní projekt:

```bash
tmux lsp -a -f '#{m:*muj-projekt,#{pane_current_path}}' \
  -F '#{session_name}:#{window_index} #{window_name}'
```

`#{m:vzor,hodnota}` porovnává stylem fnmatch (`*`, `?`), `#{m/r:vzor,hodnota}`
regexem. Stejný filtr bere i `lsw` a `ls`.

---

## Automatizace a skriptování

tmux se dá použít jako headless terminál: skript v něm nastartuje prostředí,
pošle mu vstup a přečte, co se objevilo na obrazovce. Tudy se testují TUI
aplikace, tudy si sahají do terminálu AI agenti a na tomhle stojí i
tmuxinator.

Sekce je psaná tak, aby se dala číst samostatně — pár příkazů se proto opakuje
z [Méně známé triky](#méně-známé-triky), kde jsou vysvětlené i z pohledu běžné
interaktivní práce.

### Vlastní server a deterministická velikost

```bash
tmux -L ci new-session -d -s app -x 200 -y 50 -c ~/projekt
# …práce…
tmux -L ci kill-server
```

`-L jmeno` znamená vlastní socket, a tedy vlastní server: vlastní sessions,
vlastní konfigurace a `kill-server`, který nesáhne na tvůj denní tmux. Pro
skripty je to skoro vždycky správná volba.

Kromě izolace to řeší velikost okna. Na sdíleném serveru platí
`window-size latest`, takže okno dostane velikost naposledy použitého klienta
a `-x`/`-y` se zahodí. Na vlastním serveru žádný klient není, takže platí, co
zadáš — a bez `-x`/`-y` je to 80×24. Pro skript, který výstup grepuje, je tohle
zásadní: šířka panu určuje, kde se řádky zalomí.

### Poslat vstup

```bash
tmux -L ci send-keys -t app 'make test' Enter   # text a Enter jsou dva argumenty
tmux -L ci send-keys -t app C-c                 # Ctrl-C běžícímu programu
tmux -L ci send-keys -t app -l 'Enter'          # -l = literálně, ne jméno klávesy
```

`send-keys` posílá **klávesy**, ne příkaz: `Enter` musí být samostatný argument
a bez `-l` by se slovo `Enter` uprostřed textu vzalo jako klávesa. A protože jde
o klávesy, je tmuxu jedno, jestli je na druhé straně shell vůbec připravený —
viz [Na co si dát pozor](#na-co-si-dát-pozor).

### Přečíst výstup

| Volba `capture-pane` | Co dělá |
| --- | --- |
| `-p` | Píše na stdout (jinak do tmux bufferu) |
| `-S -` | Od začátku historie — nutné pro všechno, co odscrollovalo |
| `-J` | Spojí zalomené řádky a ořízne koncové mezery |
| `-e` | Ponechá escape sekvence (barvy) |
| `-t app:0.1` | Cíl `session:window.pane` |

Capture vrací obraz obrazovky, takže dostaneš i prázdné řádky až do spodního
okraje panu. Useknutí:

```bash
tmux -L ci capture-pane -p -t app | tac | sed '/./,$!d' | tac
```

### Průběžný log (`pipe-pane`)

Capture je jednorázový snímek. Když potřebuješ úplně všechno, co proces vypsal,
napoj si na pane rouru:

```bash
tmux -L ci pipe-pane -t app 'cat >> /tmp/app.log'   # od teď logovat
tmux -L ci pipe-pane -t app                         # bez příkazu = vypnout
```

Pane může mít jen jednu rouru; další `pipe-pane` tu předchozí zavře. Volba `-o`
otevře rouru jen tehdy, když žádná neběží — díky tomu se dá stejný příkaz
nabindovat na klávesu jako přepínač, ve skriptu ji ale nechceš.

### Čekat na stav, ne na čas

Když si můžeš sáhnout do spouštěného příkazu, je nejspolehlivější `wait-for`:

```bash
tmux -L ci send-keys -t app 'make test; tmux -L ci wait-for -S hotovo' Enter
tmux -L ci wait-for hotovo
```

`wait-for kanal` blokuje, dokud někdo nepošle `wait-for -S kanal` se stejným
jménem kanálu — deterministická synchronizace tam, kde by jinak byl `sleep`
a hádání.

Když do příkazu sáhnout nemůžeš, zbývá poll na capture — čekání na to, až se na
obrazovce objeví text:

```bash
until tmux -L ci capture-pane -p -t app | grep -q 'READY'; do sleep 0.2; done
```

### Návratový kód

tmux ho ven nepropaguje. Nejjednodušší je poslat ho stranou souborem:

```bash
tmux -L ci new-session -d -s app -x 200 -y 50 \
  "make test; echo \$? > /tmp/rc; tmux -L ci wait-for -S hotovo"
tmux -L ci wait-for hotovo
exit "$(cat /tmp/rc)"
```

Nativní cesta je `remain-on-exit` — pane po doběhnutí nezmizí a výsledek zůstane
viset v `#{pane_dead_status}`:

```bash
tmux -L ci new-session -d -s app -x 200 -y 50
tmux -L ci set-option -t app remain-on-exit on
tmux -L ci respawn-pane -k -t app 'make test'

until [ "$(tmux -L ci display-message -p -t app '#{pane_dead}')" = 1 ]; do sleep 0.2; done
tmux -L ci display-message -p -t app '#{pane_dead_status}'   # → návratový kód
tmux -L ci capture-pane -p -S - -t app                       # → výstup
```

Volba musí být nastavená **dřív, než příkaz doběhne** — proto se založí prázdná
session, nastaví se `remain-on-exit` a teprve pak se do panu pustí příkaz přes
`respawn-pane -k` (`-k` zabije to, co v panu běželo předtím). Bez té volby zmizí
s panem okno a s posledním oknem celá session, takže si nestihneš přečíst nic.

A pozor: na obrazovce mrtvého panu je jen hláška `Pane is dead (status 3, …)` —
původní výstup je až ve scrollbacku, čili capture s `-S -`.

### Stav zvenčí

| Příkaz | K čemu |
| --- | --- |
| `tmux has-session -t app` | Test existence (exit 0/1) |
| `display-message -p -t app '#{pane_pid}'` | PID programu v panu |
| `display-message -p -t app '#{pane_current_command}'` | Co v panu právě běží |
| `display-message -p -t app '#{pane_dead} #{pane_dead_status}'` | Doběhlo to, a s jakým kódem |
| `tmux run-shell 'cmd'` | Spustí shell příkaz ze serveru |
| `tmux if-shell 'test -f x' 'cmd1' 'cmd2'` | Podmínka (hlavně v konfiguraci) |

Idiom „připoj se, a když session neexistuje, založ ji“ patří ve skriptu psát
přes `has-session` — `tmux new -A -s app` sice dělá totéž, ale bez terminálu
spadne na `open terminal failed`:

```bash
tmux -L ci has-session -t app 2>/dev/null || tmux -L ci new-session -d -s app
```

### Na co si dát pozor

- **Capture je obraz obrazovky, ne stream.** Progress bary, přepisy přes `\r`
  a spinnery uvidíš v tom stavu, v jakém zrovna byly. Když potřebuješ všechno,
  co proces vypsal, patří tam [`pipe-pane`](#průběžný-log-pipe-pane).
- **Šířka panu láme řádky.** Grep na dlouhý řádek selže, když ho pane zalomil —
  buď `-J`, nebo dost velké `-x`.
- **Závod po startu.** `new-session` se vrátí dřív, než je shell připravený;
  první `send-keys` může spadnout do prázdna. Počkej si na prompt, ne na
  `sleep`.
- **Úklid.** `tmux -L ci kill-server` na konci a v `trap`, jinak ti server
  přežije skript.

---

## Copy mode a schránka

| Zkratka | Co dělá |
| --- | --- |
| `prefix [` | Vstup do copy mode |
| `q` | Konec copy mode |
| šipky / `PgUp` / `PgDn` | Pohyb v historii |
| `prefix ]` | Vloží obsah tmux bufferu |
| `prefix =` | Seznam bufferů, výběr co vložit |

V copy mode s vi klávesami (`setw -g mode-keys vi`):

| Klávesa | Co dělá |
| --- | --- |
| `Space` | Začátek výběru |
| `Enter` | Zkopíruje výběr a ukončí copy mode |
| `v` | Začátek výběru (po nastavení bindingu, viz níže) |
| `y` | Zkopíruje výběr |
| `/` | Hledá vpřed |
| `?` | Hledá zpět |
| `n` / `N` | Další / předchozí výsledek |
| `g` / `G` | Začátek / konec historie |
| `H` / `M` / `L` | Horní / prostřední / dolní řádek obrazovky |

Kopírování do systémové schránky — tmux má vlastní buffery oddělené od schránky
systému, takže výběr je potřeba prohnat externím nástrojem:

```tmux
bind -T copy-mode-vi v send -X begin-selection

# Linux, X11
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "xclip -selection clipboard"

# Linux, Wayland
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "wl-copy"

# macOS
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "pbcopy"
```

Alternativně `set -g set-clipboard on` — tmux pak posílá výběr do schránky přes
escape sekvenci OSC 52, což funguje i přes SSH, ale terminál to musí podporovat
a mít povolené.

---

## Ostatní užitečné

| Zkratka | Co dělá |
| --- | --- |
| `prefix ?` | Seznam všech zkratek |
| `prefix :` | Command mode |
| `prefix t` | Velké hodiny |
| `prefix ~` | Zobrazí zprávy od tmuxu |
| `prefix Ctrl-z` | Suspendne tmux klienta |

Příkazy do shellu:

```bash
tmux list-keys                    # všechny zkratky
tmux list-commands                # všechny příkazy
tmux show-options -g              # globální nastavení
tmux display-message -a           # všechny formátovací proměnné i s hodnotami
tmux source-file ~/.tmux.conf     # znovunačte konfiguraci
tmux new -s prace 'htop'          # session rovnou spustí příkaz

# Poslat příkaz do běžící session zvenčí:
tmux send-keys -t prace:0.1 'make test' Enter
```

Cíl (`-t`) se zapisuje jako `session:window.pane`, např. `prace:0.1`. Části se
dají vynechat — `-t prace` = aktivní okno té session.

---

## Konfigurace

Konfigurace je v `~/.tmux.conf` (nebo `~/.config/tmux/tmux.conf`).
Rozumný základ:

```tmux
# Prefix na Ctrl-a (jako screen), Ctrl-b zůstává jako záloha
set -g prefix C-a
bind C-a send-prefix

# Okna a panes číslovat od 1 (0 je na klávesnici daleko)
set -g base-index 1
setw -g pane-base-index 1
set -g renumber-windows on

# Delší historie
set -g history-limit 50000

# Myš (scroll, výběr panu, resize tažením)
set -g mouse on

# Vi klávesy v copy mode
setw -g mode-keys vi

# Splity i nové okno dědí aktuální adresář
bind '"' split-window -v -c "#{pane_current_path}"
bind % split-window -h -c "#{pane_current_path}"
bind c new-window -c "#{pane_current_path}"

# Splity na klávesy, které vypadají jako výsledek
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# Rychlý reload konfigurace
unbind r
bind r source-file ~/.tmux.conf \; display "Config reloaded"

# Bez prodlevy po Escape (jinak zlobí Vim)
set -sg escape-time 10

# Focus události — Vim i TUI aplikace poznají, že pane získal/ztratil focus
set -g focus-events on

# Status zprávy zobrazovat delší dobu (default 750 ms)
set -g display-time 2000

# Barvy včetně true color (24-bit)
set -g default-terminal "tmux-256color"
set -ga terminal-features ",*:RGB"
```

Po úpravě načti buď `prefix r` (s bindingem výše), nebo
`tmux source-file ~/.tmux.conf`.

Pár detailů, které v tom zápisu nejsou samozřejmé:

- `unbind r` není potřeba (`bind r` původní binding přepíše sám), ale je to
  zvyk — defaultně `prefix r` volá `refresh-client`. Nutné je jen tehdy, když
  chceš zkratku zrušit a nic na ni nemapovat.
- `-a` u `set` znamená **append** — přidá k existující hodnotě místo přepsání.
  Proto `set -ga terminal-features ",*:RGB"` a čárka na začátku, která novou
  položku oddělí od těch už nastavených. Bez `-a` bys zahodil vše ostatní.
- `terminal-features` je serverová volba, takže se nastavuje s `-s`
  (`set -as`); `-g` u ní tmux bere taky, proto ve světě potkáš obojí.
- `#{pane_current_path}` v bindingu se vyhodnotí až při stisku zkratky, ne při
  načtení konfigurace.

### Zkratky bez prefixu (`bind -n`)

`bind` bez přepínače mapuje do tabulky `prefix`. `bind -n` (zkratka za
`-T root`) mapuje klávesu tak, že funguje **samostatně**, bez prefixu:

```tmux
# Přepínání panes Alt+šipkami bez prefixu
bind -n M-Left  select-pane -L
bind -n M-Right select-pane -R
bind -n M-Up    select-pane -U
bind -n M-Down  select-pane -D
```

Modifikátory se zapisují `C-` (Ctrl), `M-` (Alt/Meta), `S-` (Shift).

Cena je, že tu klávesu už nikdy nedostane program běžící v panu — tmux ji
sebere první. Proto se na `-n` váže jen to, co uvnitř nepotřebuješ (Alt+šipky
umí kolidovat s pohybem po slovech v shellu nebo s editory).

Defaultní `prefix Alt-šipka` (resize po 5 buňkách) tím nepřijde — ta je
v tabulce `prefix`, takže obě zkratky vedle sebe žijí bez konfliktu.

### Vlastní status bar

```tmux
set -g status-interval 5     # jak často se překresluje, v sekundách (default 15)
set -g status-style "bg=colour236,fg=colour250"
set -g status-left "#[bold] #S "
set -g status-left-length 30 # default 10 znaků delší jména session odřízne
set -g status-right "#[fg=colour244]%H:%M  %d.%m."
setw -g window-status-format " #I:#W "
setw -g window-status-current-style "bg=colour39,fg=colour232,bold"
setw -g window-status-current-format " #I:#W "
```

`window-status-format` je jedna položka v seznamu oken uprostřed,
`window-status-current-format` totéž pro aktuální okno. Ve formátech se dají
použít proměnné, devět nejčastějších má i krátký alias:

| Krátce | Dlouze | Význam |
| --- | --- | --- |
| `#S` | `#{session_name}` | Jméno session |
| `#I` | `#{window_index}` | Index okna |
| `#W` | `#{window_name}` | Jméno okna |
| `#F` | `#{window_flags}` | Příznaky okna — `*` aktivní, `-` předchozí, `Z` zoomnuté, `!` bell |
| `#P` | `#{pane_index}` | Index panu |
| `#D` | `#{pane_id}` | Unikátní ID panu (`%3`) |
| `#T` | `#{pane_title}` | Titulek panu |
| `#H` | `#{host}` | Hostname |
| `#h` | `#{host_short}` | Hostname bez domény |
| — | `#{pane_current_path}` | Pracovní adresář panu |

Aliasů je přesně těch devět. Zbytek (a je jich kolem tří stovek —
`pane_current_path`, `window_zoomed_flag`, `client_width`, …) se píše jen
dlouze. Seznam s aktuálními hodnotami vypíše `tmux display-message -a`, popis
je v `man tmux` v sekci FORMATS.

> **Alias nejde použít v modifikátoru.** Zarovnání, náhrada i podmínka berou
> jen dlouhý název proměnné — s aliasem vyjde prázdno, protože tmux ho tam
> hledá jako jméno proměnné:
>
> ```text
> # session se jmenuje "web"
> #{p14:session_name}   →  "web           "
> #{p14:#S}             →  "              "   # zůstane jen padding
> ```
>
> Krátká forma je čistá substituce, do `status-left` nebo
> `window-status-format` stačí. Jakmile potřebuješ `#{p22:…}`,
> `#{s|…|…|:…}` nebo `#{?…,…,…}` (viz [Vlastní formát](#vlastní-formát--f)),
> piš dlouhý název.

Kromě proměnných se ve status baru používá:

- `#[fg=…,bg=…,bold]` — změna stylu do konce řetězce, `#[default]` vrátí zpět
- `%H:%M`, `%d.%m.` — status řetězce procházejí strftime, takže čas a datum
- `##` — literální `#` (proto `window_flags` vrací `#` zdvojené)

`colour0`–`colour255` je 256barevná paleta; se zapnutým RGB (viz výše) můžeš
psát i `#rrggbb`. Status bar se dá přesunout nahoru přes
`set -g status-position top`.

### Titulek terminálu a panu

```tmux
set -g set-titles on
set -g set-titles-string "#S:#W"
set -g pane-border-status top
```

`set-titles` píše titulek do **hostitelského** okna terminálu (to, co vidíš
v taskbaru nebo v přepínači oken) — hodí se, když máš otevřených víc terminálů
s různými sessions. Bez `set-titles on` se `set-titles-string` neuplatní.

`pane-border-status` vypíše titulek panu do jeho rámečku (`off` je default,
dál `top` a `bottom`); obsah řídí `pane-border-format`, např.
`set -g pane-border-format " #{pane_index}: #{pane_title} "`. Titulek panu si
nastavuje program uvnitř (escape sekvencí — Claude Code to dělá průběžně sám),
ručně jde přes `:select-pane -T jmeno`. Zabere to jeden řádek z každého panu.

---

## tmux a Claude Code

Claude Code v tmuxu funguje, ale pár věcí se defaultně rozbije. Následující je
podle [oficiální dokumentace](https://code.claude.com/docs/en/terminal-config).

### Nutné minimum do `~/.tmux.conf`

```tmux
set -g allow-passthrough on
set -s extended-keys on
set -as terminal-features 'xterm*:extkeys'
set -g mouse on
```

Co která řádka řeší:

| Volba | Bez ní |
| --- | --- |
| `allow-passthrough on` | tmux spolkne desktop notifikace a progress bar, nedostanou se do vnějšího terminálu |
| `extended-keys` + `terminal-features` | tmux nerozliší Shift+Enter od Enter, takže Shift+Enter místo nového řádku odešle prompt |
| `mouse on` | kolečko myši scrolluje tmux místo Claude Code |

Platí i tehdy, když tvůj terminál Shift+Enter sám o sobě umí — tmux je uprostřed
a musí ho umět propustit.

### `/terminal-setup` pouštěj mimo tmux

Příkaz zapisuje do konfigurace **hostitelského** terminálu (VS Code, Alacritty,
Zed, …), takže ho spusť přímo v něm, ne uvnitř tmuxu nebo screenu.

Výjimka: detekci iTerm2 zvládá i zevnitř tmuxu.

### Fullscreen rendering

[Fullscreen rendering](https://code.claude.com/docs/en/fullscreen) kreslí do
alternate screen bufferu (jako `vim`), zapíná se `/tui fullscreen`. V tmuxu
k tomu patří tři věci:

- **`tmux -CC` (iTerm2 integration mode) nefunguje.** Alternate screen buffer ani
  mouse tracking tam nejsou v pořádku, double-click může rozhodit terminál.
  Normální tmux uvnitř iTerm2 (bez `-CC`) je OK.
- **tmux do řady 3.6 včetně nemá synchronized output**, takže uvidíš víc blikání
  než mimo tmux. Novější tmux si Claude Code detekuje sám.
- **Konverzace není v nativním scrollbacku**, takže ji tmux copy mode nevidí.
  Řešení: `Ctrl-o` (transcript mode) a pak `[` — vysype celou konverzaci do
  nativního scrollbacku a tam už se dá hledat přes `prefix [` jako cokoli jiného.

### Kolize s copy mode a výběrem myší

Když Claude Code zachytává myš, nativní výběr tažením přestane fungovat — výběr
žije uvnitř aplikace, ne v tmuxu. Uvnitř tmuxu Claude Code zapisuje výběr i do
tmux paste bufferu, takže `prefix ]` ho vloží.

Pro jednorázový nativní výběr podrž `Shift` (v iTerm2 `Option`, v Terminal.app
`Fn`) a táhni myší. Když chceš nativní výběr trvale:

```bash
CLAUDE_CODE_DISABLE_MOUSE=1 claude          # bez zachytávání myši úplně
CLAUDE_CODE_DISABLE_MOUSE_CLICKS=1 claude   # kolečko funguje, kliky ne
```

### Prefix koliduje s Ctrl-b

Claude Code používá `Ctrl-b` pro odeslání tasku na pozadí. V tmuxu je to
defaultní prefix, takže ho musíš zmáčknout **dvakrát**. Další důvod, proč si
prefix přemapovat na `Ctrl-a`.

### Agent teams ve split panes

[Agent teams](https://code.claude.com/docs/en/agent-teams) umí běžet ve split-pane
režimu, kdy každý teammate dostane vlastní pane. Ten stojí přímo na tmuxu —
alternativou je jen iTerm2 s `it2` CLI. Ve VS Code, Windows Terminalu ani
Ghostty nefunguje.

Agent teams jsou experimentální a defaultně vypnuté — nejdřív je musíš zapnout
přes `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (v prostředí nebo v
`settings.json`). Bez toho se žádný team nezaloží.

```json
// ~/.claude/settings.json
{
  "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" },
  "teammateMode": "auto"
}
```

`"in-process"` je default (všichni v jednom terminálu), `"auto"` zapne split
panes, když už v tmuxu jsi, `"tmux"` je vynutí. Jednorázově
`claude --teammate-mode auto`.

Když po skončení session zůstane viset osiřelá tmux session:

```bash
tmux ls
tmux kill-session -t <jmeno>
```

---

## Pluginy

tmux **žádné plugin API nemá**. „Plugin“ je obyčejný git repozitář se shell
skripty, které za tebe volají tytéž příkazy, jaké píšeš do `~/.tmux.conf`:
`bind-key`, `set-option`, `set-hook`. Stojí to na třech vestavěných
mechanismech:

1. **`run-shell`** — tmux příkaz, který spustí externí skript. Plugin má
   v kořeni spustitelný soubor `*.tmux` a ten při načtení konfigurace
   „doinstaluje“ svoje bindingy a options.
2. **User options `@nazev`** — tmux dovolí nastavit libovolnou volbu začínající
   `@` (`set -g @demo ahoj`, přečte `show -g @demo`). Přes ně se pluginy
   konfigurují.
3. **`#(prikaz)` ve status baru** — formáty umí spustit shell příkaz a vložit
   jeho výstup. Takhle fungují všechny status-bar moduly (baterie, CPU, …).

### TPM

Pluginy se obvykle spravují přes [TPM](https://github.com/tmux-plugins/tpm)
(tmux plugin manager) — sám o sobě jen krátký shell skript:

```bash
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

```tmux
# ~/.tmux.conf
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-resurrect'

run '~/.tmux/plugins/tpm/tpm'    # musí být poslední řádek konfigurace
```

| Zkratka | Co dělá |
| --- | --- |
| `prefix I` | Naklonuje pluginy do `~/.tmux/plugins/` a aktivuje je |
| `prefix U` | Aktualizuje pluginy (git pull) |
| `prefix Alt-u` | Smaže pluginy, které už v konfiguraci nejsou |

### Nejpoužívanější pluginy

| Plugin | Co dělá |
| --- | --- |
| [tmux-resurrect](https://github.com/tmux-plugins/tmux-resurrect) | Uloží a obnoví sessions/okna/panes **přes restart stroje** (`prefix Ctrl-s` / `Ctrl-r`) |
| [tmux-continuum](https://github.com/tmux-plugins/tmux-continuum) | Nadstavba resurrectu — ukládá automaticky a obnoví při startu serveru |
| [tmux-yank](https://github.com/tmux-plugins/tmux-yank) | Kopírování do systémové schránky napříč OS |
| [vim-tmux-navigator](https://github.com/christoomey/vim-tmux-navigator) | `Ctrl-h/j/k/l` přechází bezešvě mezi Vim splity a tmux panes (párový plugin do Vimu) |
| [tmux-thumbs](https://github.com/fcsonline/tmux-thumbs), [tmux-fingers](https://github.com/Morantron/tmux-fingers) | Vimium styl: přes obrazovku se rozsvítí hinty a jednou klávesou zkopíruješ URL/hash/cestu |
| [extrakto](https://github.com/laktak/extrakto), [tmux-fzf](https://github.com/sainnhe/tmux-fzf) | fzf výběr čehokoli z výstupu — tokeny do příkazové řádky bez myši |
| [catppuccin/tmux](https://github.com/catppuccin/tmux), [dracula/tmux](https://github.com/dracula/tmux) | Témata / hotový status bar |
| [tmux-battery](https://github.com/tmux-plugins/tmux-battery), [tmux-cpu](https://github.com/tmux-plugins/tmux-cpu) | Moduly do status baru |
| [tmux-sensible](https://github.com/tmux-plugins/tmux-sensible) | Sada „rozumných defaultů“ |

Jediný z nich, který umí něco, co tmux sám vůbec neumí, je **tmux-resurrect** —
server nepřežije reboot a resurrect je na to standardní odpověď. Pokud si máš
nainstalovat jediný plugin, je to tenhle.

### Co už je dnes vestavěné

Část ekosystému zastarala, protože tmux funkce mezitím vstřebal:

- **tmux-copycat** (regex hledání) — od tmuxu 3.1 je regex hledání vestavěné
  v [copy mode](#copy-mode-a-schránka).
- **tmux-yank** — z velké části ho nahradí `set -g set-clipboard on` (OSC 52)
  nebo tři řádky s `copy-pipe-and-cancel`, viz
  [Copy mode a schránka](#copy-mode-a-schránka).
- **tmux-prefix-highlight** — jeden řádek s `#{?client_prefix,…}`, viz
  [Status bar ví, že jsi zmáčkl prefix](#status-bar-ví-že-jsi-zmáčkl-prefix).
- **tmux-sensible** — půlka jeho nastavení se s moderním tmuxem už kryje.

Obvyklá rada: začni bez pluginů a sáhni po TPM, až budeš chtít resurrect nebo
thumbs.
