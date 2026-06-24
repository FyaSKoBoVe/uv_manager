import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import threading
import queue
import os
import sys
import shutil
import platform
import webbrowser

# ============================================================================
# RILEVAZIONE SISTEMA OPERATIVO
# ============================================================================
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

# ============================================================================
# DOCUMENTAZIONE HELP
# ============================================================================
HELP_TEXTS = {
    "overview": """UV - GESTORE PACCHETTI PYTHON ULTRA-VELOCE

UV è un gestore di pacchetti e progetti Python scritto in Rust da Astral
(gli stessi creatori di Ruff). È estremamente veloce (10-100x più di pip)
e sostituisce: pip, pip-tools, virtualenv, pyenv, poetry, pipx.

CARATTERISTICHE PRINCIPALI:
• Risoluzione e installazione di pacchetti in millisecondi
• Gestione automatica degli ambienti virtuali
• Supporto nativo per pyproject.toml e uv.lock
• Gestione di multiple versioni di Python
• Cache globale condivisa tra progetti
• Compatibile con PyPI e indici privati

SITO UFFICIALE: https://docs.astral.sh/uv/
""",
    "init": """UV INIT - Inizializza un nuovo progetto Python

SINTASSI: uv init [NOME_PROGETTO] [OPZIONI]

COSA FA:
Crea una nuova cartella di progetto con la struttura minima necessaria:
• pyproject.toml (metadata del progetto e dipendenze)
• README.md
• Cartella src/ o hello.py di esempio
• .python-version (opzionale)

ESEMPI:
  uv init mio_progetto           # Crea progetto nella cartella mio_progetto
  uv init --lib mia_libreria     # Crea struttura per libreria (con src/)
  uv init --app mia_app          # Crea struttura per applicazione
  uv init --python 3.12          # Specifica versione Python

OPZIONI COMUNI:
  --name NOME         Nome del progetto
  --package           Crea come pacchetto installabile
  --lib               Struttura per libreria
  --app               Struttura per applicazione (default)
  --python VERSIONE   Versione Python da usare
  --no-readme         Non creare README.md
  --vcs git           Inizializza con git (default)
  --no-vcs            Non inizializzare git
""",
    "add": """UV ADD - Aggiungi dipendenze al progetto

SINTASSI: uv add <PACCHETTO> [PACCHETTI...] [OPZIONI]

COSA FA:
Aggiunge uno o più pacchetti come dipendenze del progetto. Aggiorna
automaticamente pyproject.toml e uv.lock, e installa i pacchetti
nell'ambiente virtuale.

ESEMPI:
  uv add requests                    # Aggiungi requests
  uv add requests flask              # Aggiungi più pacchetti
  uv add 'numpy>=1.26'              # Con vincolo di versione
  uv add --dev pytest               # Come dipendenza di sviluppo
  uv add --group docs sphinx        # In un gruppo specifico
  uv add --optional pdf reportlab   # Come dipendenza opzionale
  uv add 'pkg[extra1,extra2]'       # Con extras

OPZIONI COMUNI:
  --dev, -d          Aggiungi come dipendenza di sviluppo
  --group NOME       Aggiungi a un gruppo specifico
  --optional NOME    Aggiungi come dipendenza opzionale
  --editable, -e     Installa in modalità editable (per sviluppo locale)
  --raw              Aggiungi senza normalizzare la specifica
  --frozen           Non aggiornare uv.lock
  --no-sync          Non sincronizzare l'ambiente
""",
    "remove": """UV REMOVE - Rimuovi dipendenze dal progetto

SINTASSI: uv remove <PACCHETTO> [PACCHETTI...] [OPZIONI]

COSA FA:
Rimuove uno o più pacchetti dalle dipendenze del progetto. Aggiorna
pyproject.toml e uv.lock, e rimuove i pacchetti dall'ambiente virtuale.

ESEMPI:
  uv remove requests              # Rimuovi requests
  uv remove requests flask        # Rimuovi più pacchetti
  uv remove --dev pytest          # Rimuovi da dipendenze di sviluppo
  uv remove --group docs sphinx   # Rimuovi da un gruppo

OPZIONI COMUNI:
  --dev, -d          Rimuovi dalle dipendenze di sviluppo
  --group NOME       Rimuovi da un gruppo specifico
  --optional NOME    Rimuovi dalle dipendenze opzionali
  --frozen           Non aggiornare uv.lock
  --no-sync          Non sincronizzare l'ambiente
""",
    "sync": """UV SYNC - Sincronizza l'ambiente con il lockfile

SINTASSI: uv sync [OPZIONI]

COSA FA:
Sincronizza l'ambiente virtuale del progetto con le dipendenze
specificate in pyproject.toml e uv.lock. Installa, aggiorna o rimuove
pacchetti per far corrispondere esattamente l'ambiente al lockfile.

ESEMPI:
  uv sync                     # Sincronizza ambiente completo
  uv sync --dev               # Includi dipendenze di sviluppo
  uv sync --all-groups        # Includi tutti i gruppi
  uv sync --group test        # Solo un gruppo specifico
  uv sync --no-dev            # Escludi dev dependencies
  uv sync --frozen            # Usa lockfile esistente, non aggiornarlo
  uv sync --inexact           # Rimuovi pacchetti non nel lockfile

OPZIONI COMUNI:
  --dev, -d            Includi dipendenze di sviluppo
  --no-dev             Escludi dipendenze di sviluppo
  --all-groups         Includi tutti i gruppi di dipendenze
  --group NOME         Includi un gruppo specifico
  --frozen             Non aggiornare uv.lock
  --locked             Verifica che uv.lock sia aggiornato
  --inexact            Rimuovi pacchetti extra dall'ambiente
  --no-install-project Non installare il progetto stesso
""",
    "lock": """UV LOCK - Aggiorna il lockfile senza installare

SINTASSI: uv lock [OPZIONI]

COSA FA:
Aggiorna il file uv.lock con le dipendenze risolte, ma NON le installa
nell'ambiente virtuale.

ESEMPI:
  uv lock                    # Aggiorna uv.lock
  uv lock --upgrade          # Aggiorna tutte le dipendenze
  uv lock --upgrade-package requests  # Aggiorna solo requests

OPZIONI COMUNI:
  --upgrade, -U              Aggiorna tutte le dipendenze
  --upgrade-package PKG      Aggiorna solo un pacchetto specifico
  --locked                   Verifica che il lockfile sia aggiornato
  --check                    Verifica senza scrivere
""",
    "run": """UV RUN - Esegui comandi nell'ambiente del progetto

SINTASSI: uv run [OPZIONI] <COMANDO> [ARGOMENTI...]

COSA FA:
Esegue un comando assicurandosi che l'ambiente virtuale sia sincronizzato
e disponibile. Se l'ambiente non esiste, viene creato automaticamente.

ESEMPI:
  uv run python main.py                # Esegui script Python
  uv run pytest                        # Esegui pytest
  uv run ruff check .                  # Esegui ruff
  uv run --with requests python -c "..."  # Con pacchetti temporanei
  uv run --script script.py            # Esegui script con inline metadata

OPZIONI COMUNI:
  --with PACCHETTO       Aggiungi pacchetti temporanei all'esecuzione
  --all-extras           Includi tutti gli extras
  --extra NOME           Includi un extra specifico
  --no-sync              Non sincronizzare prima di eseguire
  --frozen               Non aggiornare uv.lock
  --isolated             Usa ambiente isolato temporaneo
  --script               Esegui come script PEP 723
""",
    "pip_install": """UV PIP INSTALL - Installa pacchetti (modalità pip)

SINTASSI: uv pip install <PACCHETTO> [OPZIONI]

COSA FA:
Modalità compatibile con pip per installare pacchetti in un ambiente
virtuale. Utile quando non si usa pyproject.toml.

DIFFERENZA CON "uv add":
• uv add → modifica pyproject.toml (gestione progetto)
• uv pip install → installa direttamente (stile pip classico)

ESEMPI:
  uv pip install requests                     # Installa pacchetto
  uv pip install -r requirements.txt          # Da file requirements
  uv pip install -e .                         # Installa progetto corrente
  uv pip install 'numpy>=1.26,<2.0'          # Con vincoli
  uv pip install --python 3.11 requests       # In ambiente Python 3.11
  uv pip install --system requests            # Nell'ambiente di sistema

OPZIONI COMUNI:
  -r, --requirement FILE   File requirements.txt
  -e, --editable           Installa in modalità editable
  --python VERSIONE        Python target
  --system                 Installa nell'ambiente di sistema
  --prefix PERCORSO        Installa in un prefix
  --upgrade, -U            Aggiorna pacchetti
  --reinstall              Reinstalla tutti i pacchetti
  --no-deps                Non installare dipendenze
""",
    "pip_uninstall": """UV PIP UNINSTALL - Disinstalla pacchetti

SINTASSI: uv pip uninstall <PACCHETTO> [PACCHETTI...] [OPZIONI]

COSA FA:
Rimuove pacchetti dall'ambiente virtuale corrente.

ESEMPI:
  uv pip uninstall requests              # Disinstalla pacchetto
  uv pip uninstall requests flask        # Più pacchetti
  uv pip uninstall -r requirements.txt   # Da file requirements
  uv pip uninstall --system requests     # Dall'ambiente di sistema

OPZIONI:
  -r, --requirement FILE   File con lista pacchetti
  --python VERSIONE        Python target
  --system                 Ambiente di sistema
""",
    "pip_list": """UV PIP LIST - Elenca pacchetti installati

SINTASSI: uv pip list [OPZIONI]

COSA FA:
Mostra tutti i pacchetti installati nell'ambiente virtuale corrente
con le relative versioni.

ESEMPI:
  uv pip list                    # Lista completa
  uv pip list --outdated         # Solo pacchetti obsoleti
  uv pip list --format json      # Output in formato JSON
  uv pip list --editable         # Solo pacchetti editable

OPZIONI:
  --outdated             Mostra solo pacchetti con aggiornamenti
  --editable             Solo pacchetti in modalità editable
  --format FORMATTO      Output: columns, freeze, json (default: columns)
  --python VERSIONE      Python target
""",
    "pip_freeze": """UV PIP FREEZE - Output in formato requirements.txt

SINTASSI: uv pip freeze [OPZIONI]

COSA FA:
Stampa i pacchetti installati nel formato usato da requirements.txt
(nome==versione). Compatibile con pip freeze.

ESEMPI:
  uv pip freeze                    # Output standard
  uv pip freeze > requirements.txt # Salva su file
  uv pip freeze --python 3.11      # Per specifico Python
""",
    "pip_show": """UV PIP SHOW - Mostra informazioni su un pacchetto

SINTASSI: uv pip show <PACCHETTO> [PACCHETTI...]

COSA FA:
Mostra informazioni dettagliate su uno o più pacchetti installati:
versione, percorso, dipendenze, metadata, ecc.

ESEMPI:
  uv pip show requests             # Info su requests
  uv pip show requests flask       # Info su più pacchetti
""",
    "pip_check": """UV PIP CHECK - Verifica compatibilità dipendenze

SINTASSI: uv pip check [OPZIONI]

COSA FA:
Verifica che tutte le dipendenze installate abbiano versioni compatibili
tra loro.

ESEMPI:
  uv pip check                     # Verifica ambiente corrente
  uv pip check --python 3.11       # Verifica per Python specifico
""",
    "pip_compile": """UV PIP COMPILE - Compila requirements.in in requirements.txt

SINTASSI: uv pip compile requirements.in [OPZIONI]

COSA FA:
Risolve le dipendenze da un file requirements.in e genera un
requirements.txt completo con tutte le dipendenze transitive.

ESEMPI:
  uv pip compile requirements.in                    # Compila
  uv pip compile requirements.in -o reqs.txt        # Output specifico
  uv pip compile requirements.in --upgrade          # Aggiorna tutto
  uv pip compile pyproject.toml                     # Da pyproject.toml

OPZIONI:
  -o, --output-file FILE   File di output
  --upgrade, -U            Aggiorna tutte le dipendenze
  --upgrade-package PKG    Aggiorna pacchetto specifico
  --universal              Genera per tutte le piattaforme
  --python-version VER     Versione Python target
""",
    "pip_sync": """UV PIP SYNC - Sincronizza ambiente con requirements.txt

SINTASSI: uv pip sync requirements.txt [OPZIONI]

COSA FA:
Sincronizza l'ambiente virtuale con un file requirements.txt.

ESEMPI:
  uv pip sync requirements.txt           # Sincronizza
  uv pip sync requirements.txt --dry-run # Mostra cosa farebbe
  uv pip sync req1.txt req2.txt          # Più file

OPZIONI:
  --dry-run              Mostra azioni senza eseguirle
  --python VERSIONE      Python target
  --system               Ambiente di sistema
""",
    "python_install": """UV PYTHON INSTALL - Installa versioni di Python

SINTASSI: uv python install [VERSIONI...] [OPZIONI]

COSA FA:
Scarica e installa versioni standalone di Python gestite da uv.

ESEMPI:
  uv python install                    # Installa versione default
  uv python install 3.12               # Installa Python 3.12
  uv python install 3.11 3.12 3.13     # Più versioni
  uv python install 3.12t              # Python 3.12 con free-threading
  uv python install cpython-3.12       # Specifica implementazione
  uv python install --preview 3.14     # Versioni in anteprima

OPZIONI:
  --mirror URL           Mirror per download
  --force                Reinstalla anche se esiste
  --clean                Rimuovi download temporanei
  --preview              Includi versioni preview
""",
    "python_list": """UV PYTHON LIST - Elenca versioni Python disponibili

SINTASSI: uv python list [OPZIONI]

COSA FA:
Mostra tutte le versioni di Python disponibili.

ESEMPI:
  uv python list                 # Tutte le versioni
  uv python list --only-installed  # Solo installate
  uv python list --all-versions  # Tutte le versioni disponibili
  uv python list --all-architectures  # Per tutte le architetture
  uv python list --all-implementations  # CPython, PyPy, GraalPy

OPZIONI:
  --only-installed         Solo versioni installate
  --only-downloads         Solo versioni scaricabili
  --all-versions           Tutte le versioni disponibili
  --all-architectures      Tutte le architetture
  --all-implementations    CPython, PyPy, GraalPy, ecc.
  --all-platforms          Tutte le piattaforme
""",
    "python_find": """UV PYTHON FIND - Trova un interprete Python

SINTASSI: uv python find [VERSIONE] [OPZIONI]

COSA FA:
Trova il percorso di un interprete Python disponibile.

ESEMPI:
  uv python find                 # Python default
  uv python find 3.12            # Python 3.12
  uv python find --system        # Solo Python di sistema
""",
    "python_pin": """UV PYTHON PIN - Fissa la versione Python del progetto

SINTASSI: uv python pin <VERSIONE> [OPZIONI]

COSA FA:
Crea o aggiorna il file .python-version nella directory corrente.

ESEMPI:
  uv python pin 3.12             # Fissa a Python 3.12
  uv python pin 3.11 --global    # Fissa globalmente
  uv python pin 3.12 --resolved  # Usa versione completa

OPZIONI:
  --global               Fissa globalmente (non nel progetto)
  --resolved             Usa versione completa risolta
""",
    "python_uninstall": """UV PYTHON UNINSTALL - Disinstalla versioni Python

SINTASSI: uv python uninstall <VERSIONI...> [OPZIONI]

COSA FA:
Rimuove versioni di Python installate tramite uv python install.

ESEMPI:
  uv python uninstall 3.11       # Disinstalla Python 3.11
  uv python uninstall 3.11 3.12  # Più versioni
  uv python uninstall --all      # Tutte le versioni gestite
""",
    "tool_install": """UV TOOL INSTALL - Installa tool CLI Python

SINTASSI: uv tool install <PACCHETTO> [OPZIONI]

COSA FA:
Installa un pacchetto Python come tool CLI globale, in un ambiente
isolato. Simile a pipx.

ESEMPI:
  uv tool install ruff           # Installa ruff
  uv tool install black          # Installa black
  uv tool install httpie         # Installa httpie
  uv tool install --force ruff   # Reinstalla
  uv tool install --python 3.12 ruff  # Con Python specifico

OPZIONI:
  --from PACCHETTO       Pacchetto da installare
  --with PACCHETTO       Aggiungi dipendenze extra
  --python VERSIONE      Python da usare
  --force                Sovrascrivi installazioni esistenti
  --editable             Installa in modalità editable
""",
    "tool_list": """UV TOOL LIST - Elenca i tool installati

SINTASSI: uv tool list [OPZIONI]

COSA FA:
Mostra tutti i tool installati tramite uv tool install.

ESEMPI:
  uv tool list                   # Lista completa
  uv tool list --show-paths      # Mostra percorsi executabili
  uv tool list --show-version-specifiers  # Mostra specifiche versione
""",
    "tool_uninstall": """UV TOOL UNINSTALL - Disinstalla un tool

SINTASSI: uv tool uninstall <TOOL> [TOOL...] [OPZIONI]

COSA FA:
Rimuove uno o più tool installati con uv tool install.

ESEMPI:
  uv tool uninstall ruff         # Disinstalla ruff
  uv tool uninstall ruff black   # Più tool
  uv tool uninstall --all        # Tutti i tool
""",
    "tool_run": """UV TOOL RUN (UVX) - Esegui tool senza installazione

SINTASSI: uv tool run <TOOL> [ARGOMENTI...]
          uvx <TOOL> [ARGOMENTI...]

COSA FA:
Esegue un tool Python in un ambiente temporaneo isolato.

ESEMPI:
  uvx ruff check .               # Esegui ruff
  uvx black --check .            # Esegui black
  uvx cowsay "Ciao!"             # Esegui cowsay
  uvx --from httpie http GET ... # Tool con nome diverso
  uvx --with requests python -c "..."  # Con dipendenze extra

OPZIONI:
  --from PACCHETTO       Pacchetto da eseguire
  --with PACCHETTO       Aggiungi dipendenze extra
  --python VERSIONE      Python da usare
  --isolated             Non usare cache globale
""",
    "venv": """UV VENV - Crea ambiente virtuale

SINTASSI: uv venv [PERCORSO] [OPZIONI]

COSA FA:
Crea un ambiente virtuale Python.

ESEMPI:
  uv venv                        # Crea .venv nella directory corrente
  uv venv mio_env                # Crea mio_env
  uv venv --python 3.12          # Con Python specifico
  uv venv --python 3.12 --seed   # Con pip e setuptools
  uv venv --system-site-packages # Accesso ai pacchetti di sistema

OPZIONI:
  --python VERSIONE      Versione Python da usare
  --seed                 Installa pip, setuptools, wheel
  --system-site-packages # Accesso ai pacchetti di sistema
  --allow-existing       Non fallire se esiste già
  --relocatable          Crea ambiente rilocabile
""",
    "build": """UV BUILD - Costruisci pacchetti distribuibili

SINTASSI: uv build [OPZIONI] [PERCORSO]

COSA FA:
Costruisce i pacchetti distribuibili (sdist e wheel).

ESEMPI:
  uv build                       # Build del progetto corrente
  uv build --sdist               # Solo sdist
  uv build --wheel               # Solo wheel
  uv build --out-dir dist_custom # Directory output custom
  uv build ./altro_progetto      # Build di altro progetto

OPZIONI:
  --package NOME         Pacchetto specifico in workspace
  --all-packages         Tutti i pacchetti in workspace
  --sdist                Solo source distribution
  --wheel                Solo wheel
  --out-dir DIR          Directory di output
  --no-sources           Non usare fonti alternative
""",
    "publish": """UV PUBLISH - Pubblica pacchetti su PyPI

SINTASSI: uv publish [OPZIONI] [FILE...]

COSA FA:
Pubblica pacchetti (sdist/wheel) su un indice come PyPI.

ESEMPI:
  uv publish                   # Pubblica da dist/
  uv publish dist/*.whl        # Pubblica wheel specifici
  uv publish --index testpypi  # Su TestPyPI
  uv publish --token ...       # Con token di autenticazione

OPZIONI:
  --index NOME           Nome indice da pyproject.toml
  --publish-url URL      URL dell'indice
  --token TOKEN          Token di autenticazione
  --username USER        Username
  --password PASS        Password
  --check-url URL        Verifica se versione esiste già
""",
    "cache": """UV CACHE - Gestisci la cache di uv

SINTASSI: uv cache <COMANDO> [OPZIONI]

COMANDI DISPONIBILI:
  uv cache dir             Mostra percorso cache
  uv cache clean           Pulisci la cache
  uv cache prune           Rimuovi entry non referenziate

ESEMPI:
  uv cache dir                     # Dove si trova la cache
  uv cache clean                   # Pulisci tutta la cache
  uv cache clean requests          # Pulisci cache di un pacchetto
  uv cache prune                   # Rimuovi entry orfane
""",
    "self_update": """UV SELF UPDATE - Aggiorna uv stesso

SINTASSI: uv self update [VERSIONE] [OPZIONI]

COSA FA:
Aggiorna uv all'ultima versione o a una versione specifica.

ESEMPI:
  uv self update                 # Aggiorna all'ultima versione
  uv self update 0.5.0           # Aggiorna a versione specifica

OPZIONI:
  --force                Forza aggiornamento
""",
    "tree": """UV TREE - Mostra albero delle dipendenze

SINTASSI: uv tree [OPZIONI]

COSA FA:
Mostra l'albero delle dipendenze del progetto in formato visuale.

ESEMPI:
  uv tree                        # Albero completo
  uv tree --outdated             # Solo dipendenze con aggiornamenti
  uv tree --universal            # Per tutte le piattaforme
  uv tree --depth 2              # Limita profondità
""",
}


class ScrollableTab(ttk.Frame):
    """Tab con scrollbar integrata per contenuti grandi - CROSS PLATFORM"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner_frame = ttk.Frame(self.canvas)
        
        self.inner_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Enter>", self._bind_mouse)
        self.canvas.bind("<Leave>", self._unbind_mouse)
    
    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _bind_mouse(self, event):
        # ✅ CROSS PLATFORM: bind diversi per Linux e Windows
        if IS_WINDOWS:
            # Windows usa solo MouseWheel
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        else:
            # Linux usa Button-4 e Button-5
            self.canvas.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel)
            # Alcuni Linux supportano anche MouseWheel
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _unbind_mouse(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        if not IS_WINDOWS:
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
    
    def _on_mousewheel(self, event):
        """Gestisce lo scroll in modo cross-platform"""
        if IS_WINDOWS:
            # Windows: event.delta è positivo su, negativo giù
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            # Linux: Button-4 su, Button-5 giù
            if hasattr(event, 'num'):
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
            elif hasattr(event, 'delta'):
                # Fallback per alcuni Linux con MouseWheel
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class UvManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UV Manager - Interfaccia Grafica Completa")
        
        # Finestra ridimensionabile
        self.root.resizable(True, True)
        
        # Apri a schermo intero
        self._open_fullscreen()
        
        self.log_queue = queue.Queue()
        self.thread = None
        self.current_process = None
        self.working_dir = tk.StringVar(value=os.getcwd())
        
        # ✅ Font cross-platform
        self.font_monospace = self._get_monospace_font()
        
        self._check_uv_installed()
        self._build_menu()
        self._build_ui()
        self._process_queue()
        
        # Posiziona il sash dopo il rendering
        self.root.after(200, self._position_console_sash)
    
    def _get_monospace_font(self):
        """Restituisce un font monospace disponibile su entrambi i sistemi"""
        if IS_WINDOWS:
            return ("Consolas", 10)  # Windows ha Consolas di default
        else:
            return ("Monospace", 10)  # Linux ha Monospace
    
    def _open_fullscreen(self):
        """Apre la finestra a schermo intero - CROSS PLATFORM"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        if IS_WINDOWS:
            # ✅ Windows: 'zoomed' funziona sempre
            try:
                self.root.state('zoomed')
                print(f"[Windows] Schermo intero attivato: {screen_width}x{screen_height}")
                return
            except tk.TclError:
                pass
        
        # Linux: prova 'zoomed' (funziona con GNOME, KDE, XFCE)
        try:
            self.root.attributes('-zoomed', True)
            print(f"[Linux] Schermo intero attivato (zoomed): {screen_width}x{screen_height}")
            return
        except tk.TclError:
            pass
        
        # Fallback: geometry alle dimensioni dello schermo
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        print(f"[Fallback] Schermo intero attivato: {screen_width}x{screen_height}")
    
    def _position_console_sash(self):
        """Posiziona il separatore per avere la console alta ~8 righe"""
        try:
            total_height = self.main_paned.winfo_height()
            if total_height < 100:
                self.root.after(100, self._position_console_sash)
                return
            
            console_height = 200
            sash_position = total_height - console_height
            if sash_position > 100:
                self.main_paned.sashpos(0, sash_position)
                print(f"[Layout] Sash posizionato a {sash_position}px")
        except Exception as e:
            print(f"[Warning] Impossibile posizionare il sash: {e}")
    
    def _check_uv_installed(self):
        """Verifica che uv sia installato - MESSAGGIO CROSS PLATFORM"""
        if not shutil.which("uv"):
            if IS_WINDOWS:
                install_msg = (
                    "Il comando 'uv' non è stato trovato nel PATH.\n\n"
                    "Installalo con uno di questi metodi:\n\n"
                    "METODO 1 - PowerShell (consigliato):\n"
                    "powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"\n\n"
                    "METODO 2 - winget:\n"
                    "winget install --id=astral-sh.uv -e\n\n"
                    "METODO 3 - pip:\n"
                    "pip install uv\n\n"
                    "Dopo l'installazione, RIAVVIA il terminale."
                )
            else:
                install_msg = (
                    "Il comando 'uv' non è stato trovato nel PATH.\n\n"
                    "Installalo con:\n"
                    "curl -LsSf https://astral.sh/uv/install.sh | sh\n\n"
                    "Poi riavvia il terminale o esegui:\n"
                    "source $HOME/.local/bin/env"
                )
            
            self.root.after(100, lambda: messagebox.showwarning(
                "UV non trovato", install_msg
            ))
    
    def _build_menu(self):
        """Crea la barra dei menu con Aiuto dettagliato"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Cambia directory di lavoro...", command=self._browse_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Panoramica su uv", 
                              command=lambda: self._show_help("Panoramica su uv", HELP_TEXTS["overview"]))
        help_menu.add_separator()

        project_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title in [
            ("init", "uv init - Inizializza progetto"),
            ("add", "uv add - Aggiungi dipendenze"),
            ("remove", "uv remove - Rimuovi dipendenze"),
            ("sync", "uv sync - Sincronizza ambiente"),
            ("lock", "uv lock - Aggiorna lockfile"),
            ("run", "uv run - Esegui comandi"),
            ("tree", "uv tree - Albero dipendenze"),
        ]:
            project_menu.add_command(label=title, 
                                     command=lambda c=cmd, t=title: self._show_help(t, HELP_TEXTS[c]))
        help_menu.add_cascade(label="Comandi Progetto", menu=project_menu)

        pip_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title in [
            ("pip_install", "uv pip install"),
            ("pip_uninstall", "uv pip uninstall"),
            ("pip_list", "uv pip list"),
            ("pip_freeze", "uv pip freeze"),
            ("pip_show", "uv pip show"),
            ("pip_check", "uv pip check"),
            ("pip_compile", "uv pip compile"),
            ("pip_sync", "uv pip sync"),
        ]:
            pip_menu.add_command(label=title, 
                                 command=lambda c=cmd, t=title: self._show_help(t, HELP_TEXTS[c]))
        help_menu.add_cascade(label="Comandi Pip", menu=pip_menu)

        python_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title in [
            ("python_install", "uv python install"),
            ("python_list", "uv python list"),
            ("python_find", "uv python find"),
            ("python_pin", "uv python pin"),
            ("python_uninstall", "uv python uninstall"),
        ]:
            python_menu.add_command(label=title, 
                                    command=lambda c=cmd, t=title: self._show_help(t, HELP_TEXTS[c]))
        help_menu.add_cascade(label="Comandi Python", menu=python_menu)

        tool_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title in [
            ("tool_install", "uv tool install"),
            ("tool_list", "uv tool list"),
            ("tool_uninstall", "uv tool uninstall"),
            ("tool_run", "uv tool run / uvx"),
        ]:
            tool_menu.add_command(label=title, 
                                  command=lambda c=cmd, t=title: self._show_help(t, HELP_TEXTS[c]))
        help_menu.add_cascade(label="Comandi Tool", menu=tool_menu)

        other_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title in [
            ("venv", "uv venv - Ambiente virtuale"),
            ("build", "uv build - Costruisci pacchetti"),
            ("publish", "uv publish - Pubblica su PyPI"),
            ("cache", "uv cache - Gestione cache"),
            ("self_update", "uv self update - Aggiorna uv"),
        ]:
            other_menu.add_command(label=title, 
                                   command=lambda c=cmd, t=title: self._show_help(t, HELP_TEXTS[c]))
        help_menu.add_cascade(label="Altri Comandi", menu=other_menu)

        help_menu.add_separator()
        help_menu.add_command(label="Documentazione ufficiale", 
                              command=lambda: webbrowser.open("https://docs.astral.sh/uv/"))
        help_menu.add_command(label="Informazioni", command=self._show_about)
        menubar.add_cascade(label="Aiuto", menu=help_menu)
    
    def _show_help(self, title, text):
        """Mostra una finestra di aiuto adattiva"""
        help_win = tk.Toplevel(self.root)
        help_win.title(title)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        win_width = int(screen_width * 0.6)
        win_height = int(screen_height * 0.7)
        pos_x = int((screen_width - win_width) / 2)
        pos_y = int((screen_height - win_height) / 2)
        help_win.geometry(f"{win_width}x{win_height}+{pos_x}+{pos_y}")
        help_win.minsize(400, 300)
        help_win.transient(self.root)
        
        text_widget = scrolledtext.ScrolledText(help_win, wrap=tk.WORD, 
                                                 font=self.font_monospace,
                                                 padx=10, pady=10)
        text_widget.pack(fill="both", expand=True, padx=5, pady=5)
        text_widget.insert(tk.END, text)
        text_widget.configure(state="disabled")
        
        ttk.Button(help_win, text="Chiudi", command=help_win.destroy).pack(pady=5)
    
    def _show_about(self):
        messagebox.showinfo(
            "Informazioni",
            "UV Manager GUI\n\n"
            "Interfaccia grafica per il gestore di pacchetti uv\n"
            "Sviluppato con Python e Tkinter\n\n"
            "Compatibile con:\n"
            "• Linux (tutte le distribuzioni)\n"
            "• Windows 10/11\n\n"
            "Interfaccia adattiva per qualsiasi risoluzione\n\n"
            "Documentazione: https://docs.astral.sh/uv/\n"
            "Data: Giugno 2026"
        )
    
    def _build_ui(self):
        """Costruisce l'interfaccia principale"""
        style = ttk.Style()
        style.configure("TButton", padding=5)
        style.configure("TLabel", padding=2)
        style.configure("TLabelframe.Label", font=("Helvetica", 10, "bold"))

        # PanedWindow verticale con sash trascinabile
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.main_paned.pack(fill="both", expand=True, padx=5, pady=5)

        # PARTE SUPERIORE: Directory + Notebook
        top_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(top_frame, weight=1)

        dir_frame = ttk.LabelFrame(top_frame, text="Directory di Lavoro", padding=8)
        dir_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Entry(dir_frame, textvariable=self.working_dir).pack(
            side="left", padx=5, fill="x", expand=True
        )
        ttk.Button(dir_frame, text="Sfoglia...", command=self._browse_dir).pack(side="left", padx=5)

        self.notebook = ttk.Notebook(top_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self._build_project_tab()
        self._build_pip_tab()
        self._build_python_tab()
        self._build_tool_tab()
        self._build_build_tab()
        self._build_system_tab()

        # PARTE INFERIORE: Console (8 righe, ridimensionabile)
        bottom_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(bottom_frame, weight=0)

        console_frame = ttk.LabelFrame(bottom_frame, 
                                        text="Output Console (trascina il bordo per ridimensionare)", 
                                        padding=5)
        console_frame.pack(fill="both", expand=True, padx=5, pady=5)
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        
        self.console = scrolledtext.ScrolledText(
            console_frame, 
            wrap=tk.WORD, 
            bg="#1e1e1e", 
            fg="#4ec9b0", 
            font=self.font_monospace,
            insertbackground="white",
            height=8
        )
        self.console.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.console.configure(state="disabled")

        btn_frame = ttk.Frame(console_frame)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        ttk.Button(btn_frame, text="Pulisci Console", 
                   command=self._clear_console).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Ferma processo", 
                   command=self._stop_process).pack(side="left", padx=5)
    
    def _build_project_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text="Progetto")
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, "uv init - Crea progetto", 
                                  [("Nome progetto:", "init_name")],
                                  "init", row=0,
                                  extra_flags=[("Lib (--lib)", "init_lib"), 
                                              ("App (--app)", "init_app"),
                                              ("No README", "init_noreadme")])
        
        self._add_command_section(content, "uv add - Aggiungi dipendenza",
                                  [("Pacchetto (es. requests):", "add_pkg")],
                                  "add", row=1,
                                  extra_flags=[("Dev (--dev)", "add_dev"),
                                              ("Editable (-e)", "add_editable")])

        self._add_command_section(content, "uv remove - Rimuovi dipendenza",
                                  [("Pacchetto:", "remove_pkg")],
                                  "remove", row=2)

        self._add_command_section(content, "uv sync - Sincronizza ambiente",
                                  [], "sync", row=3,
                                  extra_flags=[("Dev (--dev)", "sync_dev"),
                                              ("No dev (--no-dev)", "sync_nodev"),
                                              ("Frozen (--frozen)", "sync_frozen")])

        self._add_command_section(content, "uv lock - Aggiorna lockfile",
                                  [], "lock", row=4,
                                  extra_flags=[("Upgrade (-U)", "lock_upgrade")])

        self._add_command_section(content, "uv run - Esegui comando",
                                  [("Comando (es. python main.py):", "run_cmd")],
                                  "run", row=5)

        self._add_command_section(content, "uv tree - Albero dipendenze",
                                  [], "tree", row=6,
                                  extra_flags=[("Outdated", "tree_outdated")])
    
    def _build_pip_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text="Pip")
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, "uv pip install - Installa pacchetti",
                                  [("Pacchetto/i (separati da spazio):", "pip_inst_pkg")],
                                  "pip_install", row=0,
                                  extra_flags=[("Requirements (-r)", "pip_inst_req"),
                                              ("Editable (-e)", "pip_inst_edit"),
                                              ("Upgrade (-U)", "pip_inst_upgrade"),
                                              ("System", "pip_inst_system")])

        self._add_command_section(content, "uv pip uninstall - Disinstalla",
                                  [("Pacchetto/i:", "pip_uninst_pkg")],
                                  "pip_uninstall", row=1)

        self._add_command_section(content, "uv pip list - Elenca pacchetti",
                                  [], "pip_list", row=2,
                                  extra_flags=[("Outdated", "pip_list_outdated"),
                                              ("JSON", "pip_list_json")])

        self._add_command_section(content, "uv pip freeze - Output requirements",
                                  [], "pip_freeze", row=3)

        self._add_command_section(content, "uv pip show - Info pacchetto",
                                  [("Pacchetto:", "pip_show_pkg")],
                                  "pip_show", row=4)

        self._add_command_section(content, "uv pip check - Verifica dipendenze",
                                  [], "pip_check", row=5)

        self._add_command_section(content, "uv pip compile - Compila requirements",
                                  [("File input (es. requirements.in):", "pip_comp_in")],
                                  "pip_compile", row=6,
                                  extra_flags=[("Upgrade (-U)", "pip_comp_upgrade")])

        self._add_command_section(content, "uv pip sync - Sincronizza con requirements",
                                  [("File requirements.txt:", "pip_sync_file")],
                                  "pip_sync", row=7)
    
    def _build_python_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text="Python")
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, "uv python install - Installa Python",
                                  [("Versione (es. 3.12):", "py_inst_ver")],
                                  "python_install", row=0)

        self._add_command_section(content, "uv python list - Elenca Python",
                                  [], "python_list", row=1,
                                  extra_flags=[("Solo installati", "py_list_installed"),
                                              ("Tutte versioni", "py_list_all")])

        self._add_command_section(content, "uv python find - Trova interprete",
                                  [("Versione (opzionale):", "py_find_ver")],
                                  "python_find", row=2)

        self._add_command_section(content, "uv python pin - Fissa versione progetto",
                                  [("Versione (es. 3.12):", "py_pin_ver")],
                                  "python_pin", row=3)

        self._add_command_section(content, "uv python uninstall - Disinstalla Python",
                                  [("Versione:", "py_uninst_ver")],
                                  "python_uninstall", row=4)
    
    def _build_tool_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text="Tool")
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, "uv tool install - Installa tool",
                                  [("Pacchetto (es. ruff):", "tool_inst_pkg")],
                                  "tool_install", row=0,
                                  extra_flags=[("Force", "tool_inst_force")])

        self._add_command_section(content, "uv tool list - Elenca tool",
                                  [], "tool_list", row=1,
                                  extra_flags=[("Show paths", "tool_list_paths")])

        self._add_command_section(content, "uv tool uninstall - Disinstalla tool",
                                  [("Tool:", "tool_uninst_name")],
                                  "tool_uninstall", row=2)

        self._add_command_section(content, "uv tool run (uvx) - Esegui tool",
                                  [("Tool e argomenti (es. ruff check .):", "tool_run_cmd")],
                                  "tool_run", row=3)
    
    def _build_build_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text="Build/Publish")
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, "uv venv - Crea ambiente virtuale",
                                  [("Nome (opzionale, default .venv):", "venv_name")],
                                  "venv", row=0,
                                  extra_flags=[("Seed (--seed)", "venv_seed"),
                                              ("System site", "venv_sys")])

        self._add_command_section(content, "uv build - Costruisci pacchetti",
                                  [], "build", row=1,
                                  extra_flags=[("Solo sdist", "build_sdist"),
                                              ("Solo wheel", "build_wheel")])

        self._add_command_section(content, "uv publish - Pubblica su PyPI",
                                  [("File (opzionale, default dist/*):", "publish_files")],
                                  "publish", row=2)
    
    def _build_system_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text="Sistema")
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, "uv cache dir - Mostra percorso cache",
                                  [], "cache_dir", row=0)

        self._add_command_section(content, "uv cache clean - Pulisci cache",
                                  [("Pacchetto (opz., vuoto=tutto):", "cache_clean_pkg")],
                                  "cache_clean", row=1)

        self._add_command_section(content, "uv cache prune - Rimuovi entry orfane",
                                  [], "cache_prune", row=2)

        self._add_command_section(content, "uv self update - Aggiorna uv",
                                  [("Versione (opz., vuoto=ultima):", "self_ver")],
                                  "self_update", row=3)
    
    def _add_command_section(self, parent, title, fields, cmd_key, row, extra_flags=None):
        """Aggiunge una sezione comando con layout responsivo"""
        frame = ttk.LabelFrame(parent, text=title, padding=8)
        frame.grid(row=row, column=0, sticky="ew", pady=4, padx=5)

        input_frame = ttk.Frame(frame)
        input_frame.pack(fill="x", pady=2)
        
        vars_dict = {}
        
        for i, (label_text, var_name) in enumerate(fields):
            ttk.Label(input_frame, text=label_text).grid(
                row=0, column=i*2, sticky="w", padx=(5, 2)
            )
            var = tk.StringVar()
            vars_dict[var_name] = var
            entry = ttk.Entry(input_frame, textvariable=var)
            entry.grid(row=0, column=i*2+1, sticky="ew", padx=(2, 5))
            input_frame.columnconfigure(i*2+1, weight=1)
        
        flag_vars = {}
        if extra_flags:
            flag_frame = ttk.Frame(frame)
            flag_frame.pack(fill="x", pady=5)
            for label, flag_name in extra_flags:
                var = tk.BooleanVar()
                flag_vars[flag_name] = var
                ttk.Checkbutton(flag_frame, text=label, variable=var).pack(
                    side="left", padx=8
                )
        
        btn = ttk.Button(
            input_frame, text="Esegui", width=12,
            command=lambda k=cmd_key, v=vars_dict, f=flag_vars: 
                self._execute_cmd(k, v, f)
        )
        btn.grid(row=0, column=len(fields)*2, padx=5)
    
    def _execute_cmd(self, cmd_key, vars_dict, flag_vars):
        """Costruisce ed esegue il comando uv"""
        cmd = ["uv"]
        
        if cmd_key == "init":
            cmd.append("init")
            if vars_dict.get("init_name", tk.StringVar()).get():
                cmd.append(vars_dict["init_name"].get())
            if flag_vars.get("init_lib", tk.BooleanVar()).get():
                cmd.append("--lib")
            if flag_vars.get("init_app", tk.BooleanVar()).get():
                cmd.append("--app")
            if flag_vars.get("init_noreadme", tk.BooleanVar()).get():
                cmd.append("--no-readme")
        
        elif cmd_key == "add":
            cmd.append("add")
            pkg = vars_dict["add_pkg"].get().strip()
            if not pkg:
                messagebox.showerror("Errore", "Inserisci il nome del pacchetto")
                return
            cmd.extend(pkg.split())
            if flag_vars.get("add_dev", tk.BooleanVar()).get():
                cmd.append("--dev")
            if flag_vars.get("add_editable", tk.BooleanVar()).get():
                cmd.append("--editable")
        
        elif cmd_key == "remove":
            cmd.append("remove")
            pkg = vars_dict["remove_pkg"].get().strip()
            if not pkg:
                messagebox.showerror("Errore", "Inserisci il nome del pacchetto")
                return
            cmd.extend(pkg.split())
        
        elif cmd_key == "sync":
            cmd.append("sync")
            if flag_vars.get("sync_dev", tk.BooleanVar()).get():
                cmd.append("--dev")
            if flag_vars.get("sync_nodev", tk.BooleanVar()).get():
                cmd.append("--no-dev")
            if flag_vars.get("sync_frozen", tk.BooleanVar()).get():
                cmd.append("--frozen")
        
        elif cmd_key == "lock":
            cmd.append("lock")
            if flag_vars.get("lock_upgrade", tk.BooleanVar()).get():
                cmd.append("--upgrade")
        
        elif cmd_key == "run":
            cmd.append("run")
            run_cmd = vars_dict["run_cmd"].get().strip()
            if not run_cmd:
                messagebox.showerror("Errore", "Inserisci il comando da eseguire")
                return
            cmd.extend(run_cmd.split())
        
        elif cmd_key == "tree":
            cmd.append("tree")
            if flag_vars.get("tree_outdated", tk.BooleanVar()).get():
                cmd.append("--outdated")
        
        elif cmd_key == "pip_install":
            cmd.extend(["pip", "install"])
            pkg = vars_dict["pip_inst_pkg"].get().strip()
            if flag_vars.get("pip_inst_req", tk.BooleanVar()).get():
                cmd.extend(["-r", pkg])
            elif flag_vars.get("pip_inst_edit", tk.BooleanVar()).get():
                cmd.extend(["-e", pkg])
            else:
                if not pkg:
                    messagebox.showerror("Errore", "Inserisci i pacchetti")
                    return
                cmd.extend(pkg.split())
            if flag_vars.get("pip_inst_upgrade", tk.BooleanVar()).get():
                cmd.append("--upgrade")
            if flag_vars.get("pip_inst_system", tk.BooleanVar()).get():
                cmd.append("--system")
        
        elif cmd_key == "pip_uninstall":
            cmd.extend(["pip", "uninstall"])
            pkg = vars_dict["pip_uninst_pkg"].get().strip()
            if not pkg:
                messagebox.showerror("Errore", "Inserisci i pacchetti")
                return
            cmd.extend(pkg.split())
        
        elif cmd_key == "pip_list":
            cmd.extend(["pip", "list"])
            if flag_vars.get("pip_list_outdated", tk.BooleanVar()).get():
                cmd.append("--outdated")
            if flag_vars.get("pip_list_json", tk.BooleanVar()).get():
                cmd.extend(["--format", "json"])
        
        elif cmd_key == "pip_freeze":
            cmd.extend(["pip", "freeze"])
        
        elif cmd_key == "pip_show":
            cmd.extend(["pip", "show"])
            pkg = vars_dict["pip_show_pkg"].get().strip()
            if not pkg:
                messagebox.showerror("Errore", "Inserisci il pacchetto")
                return
            cmd.extend(pkg.split())
        
        elif cmd_key == "pip_check":
            cmd.extend(["pip", "check"])
        
        elif cmd_key == "pip_compile":
            cmd.extend(["pip", "compile"])
            f = vars_dict["pip_comp_in"].get().strip()
            if not f:
                messagebox.showerror("Errore", "Inserisci il file di input")
                return
            cmd.append(f)
            if flag_vars.get("pip_comp_upgrade", tk.BooleanVar()).get():
                cmd.append("--upgrade")
        
        elif cmd_key == "pip_sync":
            cmd.extend(["pip", "sync"])
            f = vars_dict["pip_sync_file"].get().strip()
            if not f:
                messagebox.showerror("Errore", "Inserisci il file requirements.txt")
                return
            cmd.append(f)
        
        elif cmd_key == "python_install":
            cmd.extend(["python", "install"])
            ver = vars_dict["py_inst_ver"].get().strip()
            if ver:
                cmd.extend(ver.split())
        
        elif cmd_key == "python_list":
            cmd.extend(["python", "list"])
            if flag_vars.get("py_list_installed", tk.BooleanVar()).get():
                cmd.append("--only-installed")
            if flag_vars.get("py_list_all", tk.BooleanVar()).get():
                cmd.append("--all-versions")
        
        elif cmd_key == "python_find":
            cmd.extend(["python", "find"])
            ver = vars_dict["py_find_ver"].get().strip()
            if ver:
                cmd.append(ver)
        
        elif cmd_key == "python_pin":
            cmd.extend(["python", "pin"])
            ver = vars_dict["py_pin_ver"].get().strip()
            if not ver:
                messagebox.showerror("Errore", "Inserisci la versione")
                return
            cmd.append(ver)
        
        elif cmd_key == "python_uninstall":
            cmd.extend(["python", "uninstall"])
            ver = vars_dict["py_uninst_ver"].get().strip()
            if not ver:
                messagebox.showerror("Errore", "Inserisci la versione")
                return
            cmd.extend(ver.split())
        
        elif cmd_key == "tool_install":
            cmd.extend(["tool", "install"])
            pkg = vars_dict["tool_inst_pkg"].get().strip()
            if not pkg:
                messagebox.showerror("Errore", "Inserisci il pacchetto")
                return
            cmd.append(pkg)
            if flag_vars.get("tool_inst_force", tk.BooleanVar()).get():
                cmd.append("--force")
        
        elif cmd_key == "tool_list":
            cmd.extend(["tool", "list"])
            if flag_vars.get("tool_list_paths", tk.BooleanVar()).get():
                cmd.append("--show-paths")
        
        elif cmd_key == "tool_uninstall":
            cmd.extend(["tool", "uninstall"])
            name = vars_dict["tool_uninst_name"].get().strip()
            if not name:
                messagebox.showerror("Errore", "Inserisci il nome del tool")
                return
            cmd.extend(name.split())
        
        elif cmd_key == "tool_run":
            cmd.extend(["tool", "run"])
            run_cmd = vars_dict["tool_run_cmd"].get().strip()
            if not run_cmd:
                messagebox.showerror("Errore", "Inserisci il comando")
                return
            cmd.extend(run_cmd.split())
        
        elif cmd_key == "venv":
            cmd.append("venv")
            name = vars_dict["venv_name"].get().strip()
            if name:
                cmd.append(name)
            if flag_vars.get("venv_seed", tk.BooleanVar()).get():
                cmd.append("--seed")
            if flag_vars.get("venv_sys", tk.BooleanVar()).get():
                cmd.append("--system-site-packages")
        
        elif cmd_key == "build":
            cmd.append("build")
            if flag_vars.get("build_sdist", tk.BooleanVar()).get():
                cmd.append("--sdist")
            if flag_vars.get("build_wheel", tk.BooleanVar()).get():
                cmd.append("--wheel")
        
        elif cmd_key == "publish":
            cmd.append("publish")
            files = vars_dict["publish_files"].get().strip()
            if files:
                cmd.extend(files.split())
        
        elif cmd_key == "cache_dir":
            cmd.extend(["cache", "dir"])
        
        elif cmd_key == "cache_clean":
            cmd.extend(["cache", "clean"])
            pkg = vars_dict["cache_clean_pkg"].get().strip()
            if pkg:
                cmd.append(pkg)
        
        elif cmd_key == "cache_prune":
            cmd.extend(["cache", "prune"])
        
        elif cmd_key == "self_update":
            cmd.extend(["self", "update"])
            ver = vars_dict["self_ver"].get().strip()
            if ver:
                cmd.append(ver)
        
        cmd = [c for c in cmd if c]
        
        self._log(f"\n{'='*60}\n")
        self._log(f">>> Esecuzione: {' '.join(cmd)}\n")
        self._log(f">>> Directory: {self.working_dir.get()}\n")
        self._log(f">>> Sistema: {'Windows' if IS_WINDOWS else 'Linux'}\n")
        self._log(f"{'='*60}\n")
        
        self._run_command(cmd)
    
    def _run_command(self, cmd):
        """Esegue il comando in un thread separato - CROSS PLATFORM"""
        if self.thread and self.thread.is_alive():
            messagebox.showwarning("Attenzione", "Un comando è già in esecuzione.")
            return

        def target():
            try:
                # ✅ CROSS PLATFORM: creazione_processo
                process = subprocess.Popen(
                    cmd,
                    cwd=self.working_dir.get(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env={**os.environ, "UV_NO_PROGRESS": "1"},
                    # ✅ Windows: nasconde la finestra del processo figlio
                    creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
                )
                self.current_process = process
                for line in process.stdout:
                    self._log(line)
                process.wait()
                self._log(f"\n>>> Processo terminato con codice: {process.returncode}\n")
                self.current_process = None
            except FileNotFoundError:
                if IS_WINDOWS:
                    self._log("ERRORE: 'uv' non trovato. Installalo con:\n")
                    self._log("   winget install --id=astral-sh.uv -e\n")
                    self._log("   oppure: pip install uv\n")
                else:
                    self._log("ERRORE: 'uv' non trovato. Installalo con:\n")
                    self._log("   curl -LsSf https://astral.sh/uv/install.sh | sh\n")
                self.current_process = None
            except Exception as e:
                self._log(f"ERRORE: {str(e)}\n")
                self.current_process = None

        self.current_process = None
        self.thread = threading.Thread(target=target, daemon=True)
        self.thread.start()
    
    def _stop_process(self):
        """Ferma il processo - CROSS PLATFORM"""
        if self.current_process:
            try:
                if IS_WINDOWS:
                    # ✅ Windows: usa taskkill per terminare l'intero albero di processi
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self.current_process.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    # Linux: terminate è sufficiente
                    self.current_process.terminate()
                self._log("\nProcesso terminato dall'utente\n")
            except Exception as e:
                self._log(f"Errore terminazione: {e}\n")
        else:
            messagebox.showinfo("Info", "Nessun processo in esecuzione")
    
    def _browse_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.working_dir.set(directory)
    
    def _clear_console(self):
        self.console.configure(state="normal")
        self.console.delete(1.0, tk.END)
        self.console.configure(state="disabled")
    
    def _log(self, message):
        self.log_queue.put(message)
    
    def _process_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.console.configure(state="normal")
                self.console.insert(tk.END, msg)
                self.console.see(tk.END)
                self.console.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100, self._process_queue)


if __name__ == "__main__":
    root = tk.Tk()
    print(f"[Info] Sistema operativo rilevato: {platform.system()} {platform.release()}")
    print(f"[Info] Python: {sys.version}")
    app = UvManagerApp(root)
    root.mainloop()