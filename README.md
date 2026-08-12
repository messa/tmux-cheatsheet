# tmux cheatsheet

Poznámky a tahák k tmuxu (psáno pro tmux 3.x).

## Obsah

- [Na co je to dobré](#na-co-je-to-dobré)
- [Slovníček pojmů](#slovníček-pojmů)
- [Jak se čtou zkratky](#jak-se-čtou-zkratky)
- [Méně známé triky](#méně-známé-triky)
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
- [Historie a verze](#historie-a-verze)
- [Alternativy a příbuzné nástroje](#alternativy-a-příbuzné-nástroje)

---

## Na co je to dobré

Hlavní důvod, proč se tmux učit, je jeden:

- **Práce přežije spojení.** Pustíš na serveru migraci, build nebo
  `apt upgrade`, spadne ti SSH — a proces běží dál. Vrátíš se přes `tmux a`.
  Idiom hned po přihlášení: `tmux a || tmux` (připoj se, případně založ novou
  session); aby ses ho nemusel učit vypisovat, viz
  [Automatický start po přihlášení](#automatický-start-po-přihlášení). A když
  sis na tmux vzpomněl až ve chvíli, kdy proces už běží, není nic ztraceno —
  viz [reptyr](#reptyr-dodatečné-přehození-procesu).

Zbytek jsou věci, které dostaneš, když už ho máš:

- **Session na projekt.** Místo tabů terminálu, které zmizí s jeho zavřením,
  `tmux a -t projekt` — okna s nastavenými adresáři a rozdělanou prací přežijí
  restart terminálu, odhlášení i pád okenního správce.
- **Stejné terminály odkudkoli.** Když všechno běží v tmuxu na dev VM, je
  jedno, odkud se připojíš — počítač v kanceláři, počítač doma, tablet nebo
  mobil (např. Blink) ukážou tutéž rozdělanou práci přesně ve stavu, ve
  kterém jsi ji opustil. Práce bydlí na serveru, zařízení jsou jen okna
  do ní; z mobilu tak jde jen mrknout, jak se tváří dlouho běžící
  úloha nebo Claude Code, a případně odpovědět. Různě velkým displejům se
  okno přizpůsobuje samo — od tmuxu 3.1 se řídí zařízením, na kterém právě
  pracuješ (viz
  [velikost okna](#víc-klientů-každý-na-jiném-okně-grouped-sessions));
  na cestách pomůže kombinace s
  [mosh](#mosh-a-eternal-terminal-jiná-vrstva).
- **Panes na sledování.** Editor v jednom panu, testy ve druhém, `tail -f`
  logu ve třetím — všechno viditelné naráz.
- **Dlouho běžící proces bez systemd.** `tmux new -d -s tunel 'ssh -L …'` —
  nejrychlejší cesta k „běž na pozadí a můžu se na to kdykoli podívat“.
- **Skriptování zvenčí.** `tmux send-keys -t prace 'make test' Enter` — jeden
  skript nastartuje celé prostředí nebo pošle vstup běžící aplikaci. Na tomhle
  stojí tmuxinator i [agent teams Claude Code](#agent-teams-ve-split-panes).
- **Testování věcí, které chtějí opravdový terminál.** V CI žádné tty
  (zařízení terminálu) není — tmux ho dodá: headless server, pevně daná
  velikost okna a `capture-pane`, kterým si přečteš, co je na obrazovce.
  Takhle se testují TUI aplikace, prompty a shellové integrace. Viz
  [Automatizace a skriptování](#automatizace-a-skriptování).
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

### socket

Unixový socket — speciální soubor, přes který si dva procesy na jednom
stroji posílají data (v `ls -l` má typ `s`; nemá IP ani port, jen cestu
v souborovém systému). Každé `tmux …` v shellu je ve skutečnosti klient,
který přes socket předá příkaz serveru — proto se jiný server vybírá volbou
`-L jmeno` (jiné jméno socketu) nebo `-S /cesta/k/socketu`. Přes unixový
socket komunikuje i SSH agent, viz
[trik s reattachem](#ssh-agent-který-přežije-reattach).

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

### option (volba)

Nastavení, kterým se řídí chování tmuxu — od prefixu přes barvy po délku
historie. Podle toho, čeho se týkají, jsou čtyři druhy: server, session,
window a pane options. Nastavují se příkazem `set` (= `set-option`);
window options mají historickou zkratku `setw`. Podrobně v
[Konfiguraci](#set-vs-setw-a-druhy-options).

---

## Jak se čtou zkratky

- `prefix c` = stiskni `Ctrl-b`, pusť, pak `c`
- `Ctrl-b c` = totéž
- `tmux ls` = příkaz do shellu (mimo tmux i uvnitř)
- `:new-window` = tmux příkaz zadaný přes `prefix :`

Skoro každá zkratka má svůj příkazový ekvivalent — zkratka `prefix c` volá
příkaz `new-window`.

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
tmux -L agenti ls             # …vlastní sessions, vlastní stav options
```

Server je vázaný na socket; `-L jmeno` založí další socket (a tedy server)
vedle defaultního. Izolovaný svět — `kill-server` v něm nesáhne na tvoje
běžné sessions. Hodí se na experimenty nebo pro automatizaci, která si nemá
špinit tvůj pracovní server. Konfigurační soubory ovšem nový server čte
tytéž (`/etc/tmux.conf` i `~/.tmux.conf`, viz [Konfigurace](#konfigurace));
opravdu čistý server s defaulty dostaneš až přes `tmux -f /dev/null -L …`.

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

### SSH agent, který přežije reattach

Nejdřív krátce, co je SSH agent, protože na něm celá sekce stojí:
**ssh-agent** je proces na pozadí, který drží odemčené SSH klíče v paměti.
Passphrase zadáš jednou (`ssh-add`; často to obstará desktopové prostředí
samo) a každé další `ssh` nebo `git pull` si podpis vyžádá od agenta, místo
aby se na passphrase ptalo znovu. Programy agenta najdou přes proměnnou
`SSH_AUTH_SOCK` — je v ní cesta k unixovému socketu, přes který s agentem
mluví. `ssh-add -l` ukáže, jestli agent běží a jaké klíče drží.

**Agent forwarding** (`ssh -A server`) socket agenta „protáhne“ na server:
sshd tam vytvoří dočasný unixový socket napojený na agenta u tebe na
notebooku, takže
třeba `git pull` na serveru se podepíše tvým lokálním klíčem, aniž by klíč
kdy opustil tvůj stroj. Jenže ten dočasný socket žije jen tak dlouho jako SSH
spojení, které ho vytvořilo — a přesně z toho plyne následující problém.

Scénář: tmux běží na serveru a připojuješ se s agent forwardingem (`ssh -A`).
Po výpadku a novém přihlášení začne ve **starých** panes selhávat `git pull`
a všechno ostatní přes agenta (`Permission denied (publickey)`) —
`SSH_AUTH_SOCK` v nich ukazuje na socket zaniklého spojení.

tmux s tím napůl počítá: volba `update-environment` (jejíž součástí
`SSH_AUTH_SOCK` defaultně je) při attachi překopíruje hodnotu z nového
klienta do prostředí session. Jenže prostředí běžícího shellu zvenčí změnit
nejde — nové panes tedy fungují, staré ne. Ruční záchrana v postiženém panu:

```bash
eval "$(tmux show-env -s SSH_AUTH_SOCK)"
```

(`show-env -s` vypíše hodnotu ze session jako shellový `export`, proto
`eval`; hodí se z toho udělat alias. Patří ke světu *bez* trvalého řešení
níže — po něm už `SSH_AUTH_SOCK` v prostředí session není, žije jen
globálně (`show-env -gs`), a hlavně už záchranu nepotřebuješ.)

Trvalé řešení: nedávat shellům cestu, která se mění, ale stabilní symlink,
který každé přihlášení přehodí na živý socket:

```bash
# ~/.ssh/rc — sshd ho spustí při každém přihlášení
if [ -S "$SSH_AUTH_SOCK" ]; then
  ln -sf "$SSH_AUTH_SOCK" ~/.ssh/agent.sock
fi
```

```tmux
# ~/.tmux.conf na serveru
setenv -g SSH_AUTH_SOCK "$HOME/.ssh/agent.sock"
# a SSH_AUTH_SOCK vyndat z update-environment, ať ho attach nepřepíše zpátky:
set -g update-environment "DISPLAY KRB5CCNAME SSH_ASKPASS SSH_AGENT_PID SSH_CONNECTION WINDOWID XAUTHORITY"
```

`setenv` = `set-environment`; `-g` znamená globální prostředí serveru, ze
kterého dědí každý nový pane. Na běžícím serveru zbývá poslední krok:
sessions založené před změnou mají starou cestu zapsanou ve svém prostředí
session, a to má před globálním přednost — jednorázově ji smaž
(`tmux setenv -u SSH_AUTH_SOCK` v každé z nich), jinak jejich nové panes
dál dostávají mrtvý socket.

Dvě zrádnosti `~/.ssh/rc`. Nesmí nic psát na stdout — interaktivnímu
přihlášení to nevadí, ale rozbije to `scp`, `sftp` i `rsync`: jejich
protokol jde právě přes stdout a sshd `~/.ssh/rc` spouští i pro ně.
A jakmile soubor existuje, sshd přestane sám volat `xauth` (autentizace X11
forwardingu, viz níže) — musí ho zavolat ten skript.

Tentýž problém má i `DISPLAY` a `SSH_CONNECTION` — proto jsou
v `update-environment` taky. **X11 forwarding** (`ssh -X`) je obdoba agent
forwardingu pro grafiku: aplikace běží na serveru, její okno se kreslí na
tvém stroji. Kam kreslit, říká programům právě proměnná `DISPLAY`,
a oprávnění se prokazuje přes `xauth`. Symlink řeší jen `SSH_AUTH_SOCK`,
u zbytku zbývá `eval "$(tmux show-env -s DISPLAY)"`.

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

> **Velikost okna při různě velkých klientech.** Od tmuxu 3.1 je default
> `window-size latest`: okno má velikost klienta, který v něm naposledy
> pracoval. Střídání různě velkých zařízení tedy funguje samo od sebe —
> okno se přizpůsobí tomu, na kterém právě píšeš; na větším displeji je
> mezitím kolem okna rámeček z teček a zmizí prvním stiskem klávesy tam.
> Stará poučka „tmux se řídí nejmenším klientem“ platila do verze 2.8.
> Ladit má smysl až situaci, kdy se na totéž okno dívají dva klienti naráz
> a přeskakování velikosti vadí:
>
> ```tmux
> set -g window-size smallest    # vždy podle nejmenšího klienta (staré chování)
> set -g window-size largest     # vždy podle největšího; menší klient vidí jen výřez
> setw -g aggressive-resize on   # smallest/largest počítat jen z klientů, které okno OPRAVDU zobrazují
> ```
>
> Na `latest` nemá `aggressive-resize` vliv. A klient, který velikost nemá
> ovlivňovat nikdy (projektor, mobil jen na koukání), se připojí s
> `tmux attach -f ignore-size`.

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

Proč je to vůbec potřeba: interaktivní programy chtějí **tty** — zařízení
terminálu, ze kterého čtou klávesy a u kterého zjišťují velikost obrazovky;
podle jeho přítomnosti poznají, že s nimi mluví člověk. Skript v CI žádné
tty nemá, takže se programy chovají jinak (vypnou barvy a progress bary),
nebo rovnou odmítnou běžet. tmux tu mezeru zaplní: každý pane je
plnohodnotné tty, i když se na něj žádný člověk nedívá.

Sekce je psaná tak, aby se dala číst samostatně — pár příkazů se proto opakuje
z [Méně známé triky](#méně-známé-triky), kde jsou vysvětlené i z pohledu běžné
interaktivní práce.

### Vlastní server a deterministická velikost

```bash
tmux -L ci -f /dev/null new-session -d -s app -x 200 -y 50 -c ~/projekt
# …práce…
tmux -L ci kill-server
```

`-L jmeno` znamená vlastní socket, a tedy vlastní server: vlastní sessions,
vlastní stav options a `kill-server`, který nesáhne na tvůj denní tmux. Pro
skripty je to skoro vždycky správná volba. `-f /dev/null` k tomu vypne
načítání konfiguračních souborů (stačí u příkazu, který server startuje) —
jinak i oddělený server načte tvůj `~/.tmux.conf` a skript pak závisí na
tom, co v něm zrovna je: třeba s `base-index 1` míří všechny cíle `app:0.…`
do prázdna.

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

### Hooks: tmux reaguje sám

Zatím šlo všechno jedním směrem — skript řídí tmux. Hooks to obracejí: tmux
sám spustí příkaz, když nastane událost.

```tmux
set-hook -g client-attached 'display "vítej zpátky"'
set-hook -g after-split-window 'select-layout tiled'   # pozor: srovná i skriptované splity
```

Jména hooků jsou dvojího druhu: **události** (`session-created`,
`client-attached`, `client-detached`, `pane-died`, `pane-exited`,
`pane-focus-in`, `alert-activity`, `alert-silence`, `window-renamed`, …;
úplný seznam v `man tmux`, sekce HOOKS) a **`after-<příkaz>`**, které se
spustí po doběhnutí skoro kteréhokoli tmux příkazu (`after-new-window`,
`after-split-window`, `after-resize-pane`, …). S jednou výjimkou: příkaz
spuštěný z jiného hooku svůj after-* hook nevyvolá — hooky se neřetězí.

Pravidla hry:

- Hook spouští **tmux příkaz**, ne shell — na shell je `run-shell`. Ten ale
  bez `-b` pozdrží frontu tmux příkazů, dokud shell příkaz neskončí; cokoli
  pomalejšího pouštěj jako `run-shell -b` (na pozadí).
- Hooks jsou obyčejné options, akorát pole: `show-hooks -g` je vypíše,
  `set-hook -gu jmeno` hook zruší, bez `-g` platí jen pro aktuální session.
  `set-hook` bez indexu přepíše všechno; víc akcí na jednu událost se věší
  přes indexy — `set-hook -g 'session-created[1]' …`.
- `-g` znamená opravdu všude: hook vystřelí i pro skriptované příkazy
  a sessions, na které nemyslíš. Globální `after-split-window` výše takhle
  přerovná i split z automatizace — `split-window -l 5` pak vyrobí tiled
  pane místo pěti řádků a `-l` vypadá rozbité. Co má hlídat jedno místo,
  věš na session: `set-hook -t app …`.
- U **událostních** hooků říkají formátové proměnné, koho se událost týká:
  `#{hook_session}`, `#{hook_window}`, `#{hook_pane}` (ID),
  `#{hook_session_name}`, `#{hook_window_name}` (jména) a u `client-*`
  hooků `#{hook_client}` — jméno klienta, což je typicky jeho tty
  (`/dev/pts/3`). V `after-*` hoocích jsou všechny prázdné.
- Formáty ale expanduje jen příkaz, který to umí sám (`run-shell`,
  `display-message`, …) — `set` uvnitř hooku uloží `#{…}` doslova;
  na expanzi při zápisu je `set -F`.

Tři praktické příklady. Watchdog — spadlý proces v hlídané session se sám
nastartuje znovu (`pane-died` vyžaduje `remain-on-exit`, viz
[Návratový kód](#návratový-kód)):

```bash
tmux set-option -t app remain-on-exit on
tmux set-hook -t app pane-died 'respawn-pane'
```

Schválně bez `-g`: globální varianta udělá nesmrtelné všechny panes na
serveru — `exit` i Ctrl-D pak místo zavření panu respawnou nový shell,
všude. A příkaz, který padá hned po startu, se restartuje pořád dokola
(stovky respawnů za sekundu); brzda je udělat z hooku
`run-shell -b "sleep 1; tmux respawn-pane -t '#{hook_pane}'"`.

A desktop notifikace místo nenápadného `~` ve status baru — dotažení
[monitor-silence](#upozornění-že-příkaz-doběhl):

```tmux
setw -g monitor-silence 30   # v configu nutně s -g (žádné „aktuální okno“ tam není)
set -g silence-action any    # default „other“ vynechává aktuální okno
set-hook -g alert-silence 'run-shell -b "notify-send \"Build doběhl\""'
```

Dvě podmínky, o kterých se snadno neví: alert vystřelí, jen když je
připojený klient, a pro každé okno jen jednou — dokud se na okno znovu
nepodíváš, další cykly ticha nehlásí. A `notify-send` předpokládá desktopový
notifikační démon; na headless serveru skončí chybou a neuvidíš nic.

A evidence připojení, `hook_client` v akci — na sdíleném stroji vidíš,
které tty se kdy připojilo:

```tmux
set-hook -g client-attached 'run-shell -b "echo $(date +%F.%T) #{hook_client} >> ~/attach.log"'
```

(`$(date …)` vyhodnotí až shell při běhu hooku, proto se zaloguje skutečný
čas připojení.)

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

Dohromady to znamená, že testování přes tmux sedí na „proběhlo to a na
obrazovce je zhruba tohle“ — smoke testy, ověření, že se TUI nastartovalo
a reaguje na klávesy, kontrola návratového kódu. Na jemné asserty nad výstupem
je křehké: čteš snímek obrazovky, ne stream, a mezi „pošli klávesu“ a „přečti
výsledek“ je vždycky nějaké časování. Co jde otestovat bez terminálu, testuj
bez něj.

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

Dvě novější schopnosti copy mode (verze tmuxu v závorkách):

- **Stav hledání je ve formátech.** `#{search_present}` (od 3.2) říká,
  jestli se vůbec hledá; `#{search_count}` (od 3.5) počet shod
  (`#{search_count_partial}` = 1, dokud tmux ještě dopočítává). Hlavně pro
  skripty — `display -p` v copy mode je přečte.
- **OSC 8 hyperlinky** (od 3.4). Escape sekvence, kterou program k vypsanému
  textu přibalí neviditelné URL — obdoba `<a href>` z HTML pro terminál: na
  obrazovce je jméno souboru, kliknutím (typicky Ctrl+klik) se otevře cíl.
  Vypisuje je třeba `ls --hyperlink` nebo gcc v chybových hláškách; tmux si
  je ukládá a dává formátům: `#{mouse_hyperlink}` je cíl odkazu pod myší,
  `#{copy_cursor_hyperlink}` (od 3.5) pod kurzorem v copy mode. Otevírání
  jednou klávesou:

  ```tmux
  bind -T copy-mode-vi O if -F '#{copy_cursor_hyperlink}' 'run-shell -b "xdg-open \"#{copy_cursor_hyperlink}\""'
  ```

  (Velké `O` — malé `o` má v copy-mode-vi default, skok na druhý konec
  výběru. A `if -F` zajistí, že stisk mimo odkaz neudělá nic, místo chyby
  z `xdg-open ""`.)

  Interně to funguje vždy; aby odkazy byly klikací i ve vnějším terminálu,
  musí mít featuru `hyperlinks` — tmux ji u známých terminálů pozná sám,
  vynutí se přes `set -ga terminal-features ",*:hyperlinks"` (k zápisu viz
  [Konfigurace](#konfigurace)).

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

Konfigurace je v `~/.tmux.conf` (nebo `~/.config/tmux/tmux.conf`). Před ní
tmux načte i systémový `/etc/tmux.conf`, pokud existuje — cesta je daná při
kompilaci a distribuce ho typicky nedodávají, takže se s ním potkáš spíš na
sdílených serverech, kde ho správce použil na defaulty pro všechny účty.

Obojí se čte **jednou, při startu serveru**. Konfigurace je jen posloupnost
tmux příkazů, které se v tu chvíli provedou — nový attach ani nová session
ji znovu nenačtou, od toho je reload níže. Chyby tmux vypíše v první
session a pokračuje dalším řádkem. Vlastní soubor místo těch výchozích
vnutí `tmux -f soubor`; krajní případ `tmux -f /dev/null` spustí server
s čistými defaulty.

Rozumný základ:

```tmux
# Prefix na Ctrl-a (jako screen), Ctrl-b zůstává jako záloha
set -g prefix C-a
bind C-a send-prefix

# Okna a panes číslovat od 1 (0 je na klávesnici daleko)
set -g base-index 1
setw -g pane-base-index 1
set -g renumber-windows on

# Po zabití session přeskočit do jiné, místo vyhození z tmuxu
set -g detach-on-destroy off

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
- `detach-on-destroy off` oceníš, když sessions často zabíjíš a zakládáš
  (typicky se sessionizer skriptem): po `kill-session` tě tmux přepne do
  naposledy aktivní session, místo aby tě vyhodil na plochu. Ohleduplnější
  hodnota `no-detached` přepíná jen do sessions, ke kterým nikdo připojený
  není — a když taková není, normálně tě odpojí.

### `set` vs `setw` a druhy options

`set` je alias `set-option`, `setw` alias `set-window-option`. Options
mají čtyři druhy podle toho, čeho se týkají — server, session, window
a pane — a window options historicky měly vlastní příkaz. Dnes je `setw`
jen ekvivalent `set -w` (man page tmuxu 3.5 už `set-window-option` ani
neuvádí, příkaz zůstává kvůli kompatibilitě):

```tmux
set -s escape-time 10         # server option (jedna na celý server)
set detach-on-destroy off     # session option (bez přepínače)
set -w mode-keys vi           # window option — platí pro okno a jeho panes (= setw)
set -p allow-passthrough on   # pane option
```

Žádné `sets` ani `setp` neexistují — server a pane options se zapisují
přepínačem. A pozor na falešné kamarády: `setb` (= `set-buffer`) plní
paste buffery a `setenv` (= `set-environment`) proměnné prostředí,
s options nemají nic společného.

tmux si navíc umí druh volby odvodit ze jména (pane options odvodí jako
window), takže i holé `set mode-keys vi` funguje — `setw` v konfiguracích
přežívá ze zvyku a v tomhle taháku pro srozumitelnost: je z něj na první
pohled vidět, že volba patří oknu.

K tomu dědění: pane dědí z window options, ty z globálních window options,
session z globálních session options. Právě globální úroveň nastavuje `-g`
— proto je v `~/.tmux.conf` skoro u všeho: bez `-g` by volba platila jen
pro aktuální session nebo okno, a žádné takové při načítání konfigurace
neexistuje. Čtení: `show -g`, `show -gw`, `show -s` (`show` =
`show-options`).

### Jeden config na víc strojů (`%if`)

Konfigurák se dá větvit — bloky `%if` / `%elif` / `%else` / `%endif`
vyhodnotí tmux při načítání souboru:

```tmux
%if "#{==:#{host_short},devvm}"
set -g status-style "bg=colour52,fg=colour250"   # na dev VM červený status bar
%endif
```

Typické použití: jedny dotfiles všude a status bar obarvený podle stroje,
ať na první pohled poznáš produkci od notebooku. Podmínka je obyčejný
formát (viz [Vlastní formát](#vlastní-formát--f)), takže větvit jde podle
hostname, verze tmuxu (`#{version}`) nebo čehokoli dalšího
z `display-message -a`.

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

### Automatický start po přihlášení

Multiplexer začneš doopravdy používat až ve chvíli, kdy se spouští sám —
jinak si člověk radši otevře patnácté okno terminálu, než aby napsal `tmux`.
Do `~/.bashrc` (u login shellu na serveru `~/.bash_profile`):

```bash
case $- in *i*)
  [ -z "$TMUX" ] && command -v tmux >/dev/null && exec tmux new -A -s main
esac
```

Tři podmínky, každá tam má důvod:

- **`$-` obsahuje `i`** — jen interaktivní shell. `~/.bashrc` se načítá i při
  `scp` nebo `rsync` a spuštěný tmux by přenos rozbil.
- **`$TMUX` je prázdná** — uvnitř tmuxu je ta proměnná nastavená. Bez téhle
  podmínky by si každý nový pane spustil další tmux uvnitř tmuxu.
- **`command -v tmux`** — pojistka. S `exec` se shell nahradí tmuxem, takže
  na stroji bez tmuxu by ses jinak odřízl od přihlášení.

`exec` je volba, ne nutnost: s ním po `prefix d` rovnou končí i SSH spojení,
bez něj se vrátíš do shellu. Starší varianta téhož je
`test -z "$TMUX" && (tmux attach || tmux new-session)`; `new -A` obojí
zvládne jedním příkazem (viz [Drobnosti](#drobnosti)) a `-s main` navíc
zajistí, že se všechna přihlášení sejdou v jedné session místo hromady
sessions `0`, `1`, `2`, …

### Zámek obrazovky a úklid osiřelých sessions

tmux umí session po zadané době nečinnosti zamknout — obdoba `Ctrl-a x` ze
screenu. Typický důvod: na serverech zůstávají v odpojených sessions viset
přihlášené rootovské shelly.

```tmux
set -g lock-after-time 1800   # zamkni po 30 minutách nečinnosti (0 = nikdy)
set -g lock-command "lock -np"  # čím zamykat (tohle je i default)
bind X lock-session           # ruční zámek — defaultní zkratka na něj není
```

| Příkaz | Co zamkne |
| --- | --- |
| `lock-client` | Jednoho klienta |
| `lock-session` | Všechny klienty připojené k session |
| `lock-server` (alias `lock`) | Úplně všechny klienty na serveru |

Odemyká se heslem uživatele, pod kterým tmux běží — zamykání dělá externí
program z `lock-command`, tmux jen hlídá čas. `lock-after-time` je session
volba, takže se dá nastavit i jen pro konkrétní session (`set -t root-work`).

Zámek řeší „někdo mi sáhne na terminál“, ne „session tu visí týden“. Na to je
druhá volba:

```tmux
set -g destroy-unattached on   # session zanikne s odpojením posledního klienta
```

Pro [grouped sessions](#víc-klientů-každý-na-jiném-okně-grouped-sessions) má
navíc hodnoty `keep-last` (zruš jen tehdy, když ve skupině zůstane někdo
další) a `keep-group` (nezruš poslední session skupiny).

> **Tohle není bezpečnostní drobnost, ale vypnutí půlky tmuxu.** S `on`
> přestane dávat smysl detach — a padne i všechno, co běží bez klienta:
> `tmux new -d -s tunel …`, celá
> [Automatizace a skriptování](#automatizace-a-skriptování). Session
> založená přes `-d` zanikne okamžitě, protože k ní nikdy žádný klient
> připojený nebyl; když je poslední, skončí s ní i server. Nastavuj to
> cíleně na konkrétní session (`set -t root-work destroy-unattached on`),
> ne globálně.

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
  než mimo tmux. Synchronized output (režim 2026, zapínaný escape sekvencí
  DECSET) je dohoda mezi aplikací a terminálem: aplikace obalí celé překreslení
  obrazovky značkami „začátek/konec dávky“ a terminál ho vykreslí naráz, až
  když je dávka celá — bez toho kreslí průběžně a rozpracované mezistavy
  překreslování jsou vidět jako blikání. tmux je emulátor terminálu uprostřed,
  takže režim musí podporovat sám — umí to od verze 3.7 a Claude Code si
  novější tmux detekuje automaticky.
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
`bind-key`, `set-option`, [`set-hook`](#hooks-tmux-reaguje-sám). Stojí to na
třech vestavěných mechanismech:

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

---

## Historie a verze

### Odkud se vzal

tmux napsal **Nicholas Marriott**, vývojář OpenBSD; první commit je z léta
2007, první veřejná verze z listopadu 2007. Není to fork screenu, ale nový
kód psaný s cílem udělat BSD-licencovanou (konkrétně ISC) alternativu GNU
screenu s čistší architekturou — hlavní designové rozhodnutí je
[jeden server na všechny sessions](#slovníček-pojmů), ze kterého plyne
většina věcí, které tmux umí a screen ne. V červenci 2009 ho OpenBSD přijalo
do base systému (poprvé vyšel s OpenBSD 4.6; k tomu citát Thea de Raadta
v [sekci o screenu](#gnu-screen)) a v září 2009 vyšla verze 1.0.

### Styl vývoje a komunita

- **Domovem kódu je OpenBSD** — tmux se vyvíjí přímo v jeho CVS jako součást
  base systému. [GitHub repo](https://github.com/tmux/tmux) je „portable“
  verze: synchronizuje se z OpenBSD a přidává vrstvu přenositelnosti
  (libevent, ncurses, autotools).
- **Prakticky one-man projekt.** Z ~12 000 commitů jich přes 8 400 napsal
  Marriott sám; druhý v pořadí Thomas Adam se stará hlavně o portable větev
  a synchronizaci. Odtud i konzervativní styl: [žádné plugin API](#pluginy),
  funkce se do jádra přijímají pomalu a dokumentace je jedna důkladná man
  stránka (plus [wiki](https://github.com/tmux/tmux/wiki) na GitHubu).
- **Komunita** žije na GitHubu (issues) a v mailing listu
  `tmux-users@googlegroups.com`; ekosystém [pluginů](#pluginy) kolem TPM je
  čistě komunitní nadstavba mimo jádro.
- **Nová verze vychází zhruba jednou ročně**; písmenkové verze (3.5a, 3.6b, …)
  jsou opravné. Pozor při čtení dat z GitHubu: tag často vzniká měsíce před
  oznámením verze (3.0 je otagovaná v červnu 2019, vyšla v listopadu).

### Hlavní verze

| Verze | Vydání | Nejdůležitější novinky |
| --- | --- | --- |
| 0.1 | listopad 2007 | První veřejné vydání (tehdy na SourceForge) |
| 1.0 | září 2009 | První „kulatá“ verze, krátce po importu do OpenBSD |
| 1.8 | březen 2013 | Zoom panu (`prefix z`) |
| 2.1 | říjen 2015 | Přepsaná myš — místo čtyř voleb jediná `mouse on` |
| 2.2 | duben 2016 | True color (24bit RGB) |
| 2.4 | duben 2017 | Přepsaný copy mode: tabulky `copy-mode(-vi)`, příkazy `send -X` |
| 3.0 | listopad 2019 | Nová syntaxe konfigurace (`{}` bloky) |
| 3.1 | duben 2020 | Regex hledání v copy mode; default `window-size latest` — konec poučky „řídí se nejmenším klientem“ |
| 3.2 | duben 2021 | [Popupy](#popup-plovoucí-okno-nad-layoutem) (`display-popup`), customize mode (`prefix C`), env proměnné přes `-e` |
| 3.3 | červen 2022 | `allow-passthrough`; `server-access` — sdílení serveru mezi OS uživateli bez setuid |
| 3.4 | únor 2024 | [OSC 8 hyperlinky](#copy-mode-a-schránka); obrázky sixel (jen se sestavením `--enable-sixel`) |
| 3.5 | září 2024 | Přepracované extended keys (Shift+Enter a spol.), `search_count`, zrcadlené main-* layouty |
| 3.6 | listopad 2025 | Scrollbary u panes (`pane-scrollbars`), hlášení světlého/tmavého tématu terminálu |
| 3.7 | červen 2026 | Floating panes (zatím jen základ), synchronized output — méně blikání např. pro [Claude Code](#fullscreen-rendering) |

Úplný seznam změn je v souboru
[CHANGES](https://github.com/tmux/tmux/blob/master/CHANGES);
datované tarbally jsou na [GitHub releases](https://github.com/tmux/tmux/releases).

### Kterou verzi máš a kterou dostaneš

Vlastní verzi řekne `tmux -V`. Nejnovější upstream je **3.7b**
(červenec 2026); v balíčcích aktuálních distribucí:

| Distribuce | tmux |
| --- | --- |
| Debian 13 „trixie“ (stable) | 3.5a |
| Debian 12 „bookworm“ (oldstable) | 3.3a |
| Ubuntu 26.04 LTS „Resolute Raccoon“ | 3.6a |
| Ubuntu 24.04 LTS „Noble Numbat“ | 3.4 |

Pro tenhle tahák to znamená: na aktuálním stable Debianu i Ubuntu funguje
všechno (nejnovější zmiňované featury, `search_count`
a `copy_cursor_hyperlink`, jsou z 3.5 — bookworm a noble na ně ještě nemají).
Výjimka je synchronized output pro [Claude Code](#fullscreen-rendering) — ten
má až 3.7, která v době psaní (srpen 2026) v žádné z distribucí není.

---

## Alternativy a příbuzné nástroje

tmux nebyl první a není poslední. Rychlá mapa, co je konkurence, co doplněk
z jiné vrstvy a co jen nadstavba:

| Nástroj | Co to je | Vztah k tmuxu |
| --- | --- | --- |
| [GNU screen](https://www.gnu.org/software/screen/) | Starší multiplexer (1987) | Předchůdce; dnes hlavně sériové konzole |
| [zellij](https://zellij.dev/) | Moderní multiplexer v Rustu | Přímý konkurent s opačnou filozofií |
| [tmux-rs](https://github.com/richardscollin/tmux-rs) | Přepis tmuxu do Rustu | Experiment, zatím alpha |
| [dtach](https://github.com/crigler/dtach), [abduco](https://github.com/martanne/abduco), [zmx](https://github.com/neurosnap/zmx) | Jen detach/attach | Minimalistický výsek jedné funkce |
| [byobu](https://www.byobu.org/) | Obal nad tmuxem/screenem | Nadstavba, uvnitř běží tmux |
| [mosh](https://mosh.org/), [Eternal Terminal](https://eternalterminal.dev/) | Odolnější spojení místo SSH | Jiná vrstva, s tmuxem se kombinuje |
| [tmuxinator](https://github.com/tmuxinator/tmuxinator), [tmuxp](https://github.com/tmux-python/tmuxp) | Session managery | Nadstavba, jen skriptují tmux |
| WezTerm, kitty, iTerm2 | Terminály s vlastním multiplexingem | Částečné překrytí funkcí |
| [reptyr](https://github.com/nelhage/reptyr) | Přehodí běžící proces do jiného terminálu | Doplněk; dostane pod tmux to, cos spustil bez něj |

### GNU screen

Předchůdce z roku 1987 (tmux je z 2007) a důvod, proč si půlka světa
přemapovává prefix na `Ctrl-a` — to je defaultní prefix screenu. Základní trik
je stejný: proces na pozadí drží terminál, klient se odpojuje (`Ctrl-a d`)
a připojuje (`screen -r`).

Symbolický moment střídání stráží: v roce 2009 vzalo OpenBSD tmux do base
systému jako BSD licencovanou alternativu ke screenu — a vedle licence
rozhodovala i kvalita kódu. Theo de Raadt tehdy [v diskusi na
Undeadly](https://undeadly.org/cgi?action=article&sid=20090707041154):
„Nejpůsobivější věcí na tmux podle mě bylo, jak otravný byl audit zdrojového
kódu. Během dvou hodin jsem našel pouze jednu nebo dvě pitomosti, které měly
z bezpečnostního hlediska pouze velmi zanedbatelnou důležitost.“ (Překlad ze
[zprávičky na root.cz](https://www.root.cz/zpravicky/openbsd-do-base-importuje-tmux/).)

Hlavní rozdíly:

- **Architektura.** screen = jeden proces na session. tmux má jeden server na
  všechny sessions, a proto i příkazy, které vidí přes sessions
  (`lsp -a`, `link-window`, grouped sessions, …).
- **Splity patří klientovi.** Rozdělení okna na regiony se ve screenu detachem
  zahodí — po připojení začínáš zase s jedním. tmux má panes uložené v session,
  layout přežije. (Novější screen má `layout save`, ale je to znát, že je to
  přilepené dodatečně.)
- **Skriptovatelnost.** `screen -X stuff 'text'` a `hardcopy` proti
  `send-keys`, `capture-pane`, formátům a `wait-for` — tady je tmux
  o generaci dál; celá sekce
  [Automatizace a skriptování](#automatizace-a-skriptování) nemá ve screenu
  obdobu.
- **Vývoj.** screen léta spal; verze 5.0 (srpen 2024) přinesla přepsanou
  autentizaci a truecolor, ale koncepčně ho k tmuxu nepřiblížila.

Co screen umí a tmux ne (nebo hůř):

- **Sériová konzole:** `screen /dev/ttyUSB0 115200` — screen jako terminálový
  program pro embedded desky a síťové krabice. Dnes nejčastější důvod, proč ho
  mít nainstalovaný vedle tmuxu.
- **Multiuser napříč OS účty** býval argument pro screen (`multiuser on`
  + ACL, vyžaduje setuid binárku); tmux od 3.3 umí totéž bez setuid přes
  sdílený socket (viz [Víc serverů vedle sebe](#víc-serverů-vedle-sebe))
  a `server-access` (i read-only).

Jinak není moc důvod po screenu sahat — leda že na stroji už je a tmux tam
nedoinstaluješ.

### zellij

Nejvážnější současný konkurent, [zellij](https://zellij.dev/). Napsaný
v Rustu a jde přesně opačným směrem než tmux — místo minimálního defaultu
„baterie součástí balení“:

- **UI napovídá.** Status bar ukazuje, které klávesy v aktuálním módu
  fungují — bariéra vstupu je výrazně nižší než u tmuxu.
- **Floating panes** jako první třída (tmux má
  [popup](#popup-plovoucí-okno-nad-layoutem), ale musíš si ho nabindovat).
- **Session resurrection vestavěná** — layout a příkazy přežijí i reboot;
  v tmuxu na to potřebuješ [tmux-resurrect](#nejpoužívanější-pluginy).
- **Layouty jako soubory** (formát KDL) ve verzovacím systému — role, kterou
  u tmuxu hraje tmuxinator.
- **Skutečné plugin API** — pluginy jsou WebAssembly, ne shell skripty jako
  [u tmuxu](#pluginy).
- **Web klient** — novější verze umí session vystavit do prohlížeče (se
  sdílením přes URL).

Cena za to: znatelně víc paměti, defaultní zkratky žerou spoustu `Ctrl`
kombinací (kolidují s shellem i editory — existuje „non-colliding“ preset
a locked mód), skriptování zvenčí (`zellij action`) zdaleka nedosahuje tmux
formátů a na cizím serveru zellij skoro jistě nebude, tmux skoro jistě ano.

### tmux-rs

Kuriozita pro úplnost: [tmux-rs](https://github.com/richardscollin/tmux-rs)
je přepis tmuxu (67 000 řádků C → ~81 000 řádků Rustu) — na rozdíl od zellij
ne nový design, ale věrný port. Hobby projekt jednoho autora, zatím alpha:
skoro celý `unsafe` a se známými pády, na běžné používání to není. Česky
o něm psal
[root.cz](https://www.root.cz/zpravicky/tmux-rs-je-nova-implementace-multiplexeru-tmux-prepsana-v-jazyce-rust/).

### dtach, abduco, zmx

Opačný extrém: jen detach/attach a nic víc. Žádná okna, splity, status bar
ani scrollback (ten nechávají na terminálu).
[dtach](https://github.com/crigler/dtach) je pár set řádků C;
[abduco](https://github.com/martanne/abduco) je novější provedení téže
myšlenky (od autora [dvtm](https://github.com/martanne/dvtm), se kterým se
skládá po unixovsku: abduco = sessions, dvtm = dlaždice). Hodí se, když
chceš jen „ať to přežije odpojení“ s nulovou režií — typicky obalit jeden
dlouhoběžící proces — a multiplexer je ti zbytečný.

Moderní přírůstek téže kategorie je [zmx](https://github.com/neurosnap/zmx)
(Zig, ~1000 řádků, démon na session): taky jen attach/detach, ale při
připojení umí obnovit obsah obrazovky i scrollback — terminál emuluje přes
libghostty-vt, knihovnu vytaženou z terminálu Ghostty. Řeší tím hlavní
slabinu dtache (po attachi je obrazovka prázdná, dokud program něco
nepřekreslí). Ve stejné nice žije i [shpool](https://github.com/shell-pool/shpool)
od Googlu.

### byobu

Není alternativa, ale obal nad tmuxem (default) nebo screenem: F-klávesy
místo prefixu, hotový status bar s widgety (load, baterie, aktualizace, …).
Vyrostl z „screen-profiles“ Dustina Kirklanda z Canonicalu, jméno má podle
japonské skládací zástěny. Uvnitř běží normální tmux, takže všechno z tohohle
taháku platí — jen se s byobu občas přetahuje o konfiguraci. Dobrá volba pro
někoho, kdo se tmux učit nechce; česky
[Byobu: ještě o kousek lepší terminál](https://www.root.cz/clanky/byobu-jeste-o-kousek-lepsi-terminal/)
na root.cz.

### Terminály s vestavěným multiplexingem

- **[WezTerm](https://wezterm.org/)** má plnohodnotný vestavěný multiplexer:
  mux server, „SSH domény“, detach a attach přežije restart GUI. Ze všech
  terminálů nejblíž tomu nahradit tmux úplně.
- **[kitty](https://sw.kovidgoyal.net/kitty/)** umí taby, splity a layouty,
  ale žádný detach; autor kombinaci s tmuxem otevřeně nedoporučuje a má
  třecí plochy (např. kitty graphics protokol skrz tmux).
- **[Ghostty](https://ghostty.org/)** je z tohohle pohledu záměrně „jen“
  terminál: nativní splity a taby má, ale layout nepřežije restart aplikace
  a detach/attach neexistuje — persistenci vědomě nechává na tmuxu. Zajímavý
  je ale jako stavebnice: emulace terminálu se odděluje do knihovny
  libghostty, a nad ní vznikají nástroje jako
  [zmx](#dtach-abduco-zmx).
- **[Tilix](https://gnunn1.github.io/tilix-web/)** (GTK, Linux) umí dlaždicové
  splity, synchronizaci vstupu a „sessions“ — ty jsou ale jen uložené layouty
  na disku: žádný detach/attach, se zavřením aplikace všechno končí. Projekt
  je navíc v režimu minimální údržby a hledá maintainery.
- **iTerm2** jde opačnou cestou — `tmux -CC` ukazuje tmux okna jako nativní
  taby (viz výhrada ve [Fullscreen renderingu](#fullscreen-rendering)).

Společný háček: je to přesný opak přenositelnosti z
[Na co je to dobré](#na-co-je-to-dobré) — splity a sessions máš jen tam, kde
běží ten konkrétní terminál, a na serveru bez GUI ti nepomůžou (WezTerm mux
server je výjimka, ale vyžaduje WezTerm i na druhé straně).

### mosh a Eternal Terminal: jiná vrstva

[mosh](https://mosh.org/) neřeší sessions, ale spojení — je to náhrada SSH
pro interaktivní práci, ne multiplexer:

- běží po UDP a přežije změnu IP, uspání laptopu i výpadek sítě — spojení se
  samo obnoví,
- lokální predikce psaní: na lince s vysokou latencí vidíš, co píšeš, hned.

Co záměrně neumí: scrollback (synchronizuje jen aktuální obraz obrazovky),
detach/attach (session je svázaná s jedním klientem, z jiného stroje se k ní
nepřipojíš), port forwarding ani agent forwarding — a potřebuje otevřené UDP
porty 60000–61000.

Proto klasická kombinace **mosh + tmux**: mosh drží spojení (roaming,
latence), tmux uvnitř dodá scrollback, okna a možnost připojit se odkudkoli.
Nejsou to konkurenti, ale vrstvy.

[Eternal Terminal](https://eternalterminal.dev/) (`et`) je obdoba po TCP:
taky automatický reconnect, navíc zachovává nativní scrollback; na serveru
potřebuje běžící démon. I s ním se tmux běžně kombinuje.

### Session managery

[tmuxinator](https://github.com/tmuxinator/tmuxinator),
[tmuxp](https://github.com/tmux-python/tmuxp) a
[smug](https://github.com/ivaaaan/smug): YAML popis projektu (okna, panes,
příkazy) → jedním příkazem postavená session. Všechny jen volají totéž API
jako sekce [Automatizace a skriptování](#automatizace-a-skriptování) —
`new-window`, `send-keys`… tmuxp navíc umí `tmuxp freeze`: z běžící session
vyrobí YAML. Než po nich sáhneš, zvaž, jestli nestačí
`tmux new -A -s projekt -c ~/projekt` v aliasu nebo krátký shell skript.

### reptyr: dodatečné přehození procesu

Situace, kterou zná každý: na serveru běží hodinový build a teprve teď ti
dojde, že jsi ho nepustil v tmuxu. [reptyr](https://github.com/nelhage/reptyr)
je záchranná brzda — připojí se k běžícímu procesu přes `ptrace` (stejný
mechanismus, jakým se k cizímu procesu připojuje debugger), vymění mu
standardní vstup a výstup a hlavně **řídící terminál**, takže proces doběhne
tam, kam ho přestěhuješ:

```bash
# v původním terminálu
Ctrl-Z               # uspat na pozadí
bg                   # nechat běžet dál
disown               # odpojit od shellu, ať ho jeho ukončení nezabije
pgrep -a make        # zjistit PID

# v tmuxu
reptyr 123456
```

`bg` a `disown` jsou volitelné, ale bez nich zůstane úloha na starém
terminálu viset jako upozaděná a dá se odtamtud vytáhnout přes `fg`.

Nefunguje to vždycky:

- **`ptrace` bývá omezený.** Připojit se k cizímu procesu je citlivá
  operace, takže ji řada distribucí (Ubuntu a spol.) omezuje bezpečnostním
  modulem YAMA — reptyr pak spadne na „Operation not permitted“. Pomůže
  `sudo reptyr`, nebo dočasné povolení
  `sudo sysctl kernel.yama.ptrace_scope=0` (a potom vrátit na `1`).
- **Procesy s potomky** (shellový skript, pipeline) se přehazují celé přes
  `reptyr -T`, které převezme rovnou celou terminálovou session. Na FreeBSD
  `-T` není.
- Přehodit jde jen to, co má vlastní PID — jednu rouru uprostřed pipeline
  ne.

Česky o něm psal [Petr Krčmář na blogu
root.cz](https://blog.root.cz/petrkrcmar/prehozeni-beziciho-procesu-pod-tmuxscreen/);
ze stejné niky je i starší [retty](http://pasky.or.cz/dev/retty/) od Petra
Baudiše. Předejít celé situaci se dá
[automatickým startem tmuxu po přihlášení](#automatický-start-po-přihlášení).
