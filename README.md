# tmux cheatsheet

Poznámky a tahák k tmuxu (psáno pro tmux 3.x).

## Obsah

- [Slovníček pojmů](#slovníček-pojmů)
- [Jak se čtou zkratky](#jak-se-čtou-zkratky)
- [Sessions](#sessions)
- [Windows](#windows)
- [Panes](#panes)
- [Copy mode a schránka](#copy-mode-a-schránka)
- [Ostatní užitečné](#ostatní-užitečné)
- [Konfigurace](#konfigurace)

---

## Slovníček pojmů

### server

Proces, který běží na pozadí a drží všechny sessions, windows a panes. Startuje se
automaticky při prvním `tmux` a běží dál, i když zavřeš terminál. Proto ti věci
v tmuxu přežijí zavření okna terminálu nebo odpojení SSH.

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
(zkratky po stisku prefixu), v copy mode `copy-mode-vi` / `copy-mode`. Uvidíš to
ve výpisu `tmux list-keys`.

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

Session je ejvyšší úroveň skupiny — jedna "pracovní plocha". Obsahuje jedno nebo víc oken
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

# Splity, které dědí aktuální adresář
bind '"' split-window -v -c "#{pane_current_path}"
bind % split-window -h -c "#{pane_current_path}"

# Rychlý reload konfigurace
bind r source-file ~/.tmux.conf \; display "Config reloaded"

# Bez prodlevy po Escape (jinak zlobí Vim)
set -sg escape-time 10

# Barvy
set -g default-terminal "tmux-256color"
```

Po úpravě načti buď `prefix r` (s bindingem výše), nebo
`tmux source-file ~/.tmux.conf`.
