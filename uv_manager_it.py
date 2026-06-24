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
import json
import locale

# ============================================================================
# RILEVAZIONE SISTEMA OPERATIVO
# ============================================================================
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

# ============================================================================
# CONFIGURAZIONE E INTERNAZIONALIZZAZIONE (i18n)
# ============================================================================
CONFIG_PATH = os.path.expanduser("~/.uv_manager_config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"language": "auto"}

def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

def detect_language():
    # 1. Rileva locale di sistema
    try:
        lang, _ = locale.getdefaultlocale()
        if lang:
            prefix = lang.split('_')[0].lower()
            if prefix in ('it', 'en'):
                return prefix
    except Exception:
        pass

    try:
        lang, _ = locale.getlocale()
        if lang:
            prefix = lang.split('_')[0].lower()
            if prefix in ('it', 'en'):
                return prefix
    except Exception:
        pass

    # 2. Rileva variabili d'ambiente (Linux/macOS)
    for var in ('LANG', 'LC_ALL', 'LC_MESSAGES'):
        val = os.environ.get(var)
        if val:
            prefix = val.split('_')[0].split('.')[0].lower()
            if prefix in ('it', 'en'):
                return prefix

    # 3. Rileva lingua UI su Windows tramite ctypes
    if sys.platform == "win32":
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            if lang_id == 1040:  # 0x0410 è l'ID per l'italiano
                return "it"
        except Exception:
            pass

    return "en" # Lingua di fallback predefinita

TRANSLATIONS = {
    "it": {
        # UI Strings
        "title": "UV Manager - Interfaccia Grafica Completa",
        "menu_file": "File",
        "menu_browse_dir": "Cambia directory di lavoro...",
        "menu_exit": "Esci",
        "menu_help": "Aiuto",
        "menu_overview": "Panoramica su uv",
        "menu_proj_cmds": "Comandi Progetto",
        "menu_pip_cmds": "Comandi Pip",
        "menu_py_cmds": "Comandi Python",
        "menu_tool_cmds": "Comandi Tool",
        "menu_other_cmds": "Altri Comandi",
        "menu_official_doc": "Documentazione ufficiale",
        "menu_about": "Informazioni",
        "menu_lang": "Lingua (Language)",
        "menu_lang_auto": "Rilevamento automatico",
        "menu_lang_en": "English",
        "menu_lang_it": "Italiano",
        "msg_lang_changed": "Lingua modificata",
        "msg_lang_restart": "Riavvia l'applicazione per applicare la nuova lingua.",
        
        # Labels and Frames
        "frame_working_dir": "Directory di Lavoro",
        "btn_browse": "Sfoglia...",
        "frame_console_title": "Output Console (trascina il bordo per ridimensionare)",
        "btn_clear_console": "Pulisci Console",
        "btn_stop_process": "Ferma processo",
        "tab_project": "Progetto",
        "tab_pip": "Pip",
        "tab_python": "Python",
        "tab_tool": "Tool",
        "tab_build_publish": "Build/Publish",
        "tab_system": "Sistema",
        "btn_execute": "Esegui",
        "btn_close": "Chiudi",
        
        # Command Section Titles
        "title_init": "uv init - Crea progetto",
        "title_add": "uv add - Aggiungi dipendenza",
        "title_remove": "uv remove - Rimuovi dipendenza",
        "title_sync": "uv sync - Sincronizza ambiente",
        "title_lock": "uv lock - Aggiorna lockfile",
        "title_run": "uv run - Esegui comando",
        "title_tree": "uv tree - Albero dipendenze",
        "title_pip_install": "uv pip install - Installa pacchetti",
        "title_pip_uninstall": "uv pip uninstall - Disinstalla",
        "title_pip_list": "uv pip list - Elenca pacchetti",
        "title_pip_freeze": "uv pip freeze - Output requirements",
        "title_pip_show": "uv pip show - Info pacchetto",
        "title_pip_check": "uv pip check - Verifica dipendenze",
        "title_pip_compile": "uv pip compile - Compila requirements",
        "title_pip_sync": "uv pip sync - Sincronizza con requirements",
        "title_python_install": "uv python install - Installa Python",
        "title_python_list": "uv python list - Elenca Python",
        "title_python_find": "uv python find - Trova interprete",
        "title_python_pin": "uv python pin - Fissa versione progetto",
        "title_python_uninstall": "uv python uninstall - Disinstalla Python",
        "title_tool_install": "uv tool install - Installa tool",
        "title_tool_list": "uv tool list - Elenca tool",
        "title_tool_uninstall": "uv tool uninstall - Disinstalla tool",
        "title_tool_run": "uv tool run (uvx) - Esegui tool",
        "title_venv": "uv venv - Crea ambiente virtuale",
        "title_build": "uv build - Costruisci pacchetti",
        "title_publish": "uv publish - Pubblica su PyPI",
        "title_cache_dir": "uv cache dir - Mostra percorso cache",
        "title_cache_clean": "uv cache clean - Pulisci cache",
        "title_cache_prune": "uv cache prune - Rimuovi entry orfane",
        "title_self_update": "uv self update - Aggiorna uv",
        "title_cache": "uv cache - Gestione cache",
        
        # Form Fields & Flags
        "lbl_project_name": "Nome progetto:",
        "chk_lib": "Lib (--lib)",
        "chk_app": "App (--app)",
        "chk_noreadme": "No README",
        "lbl_pkg_add": "Pacchetto (es. requests):",
        "chk_dev": "Dev (--dev)",
        "chk_editable": "Editable (-e)",
        "lbl_pkg_remove": "Pacchetto:",
        "chk_no_dev": "No dev (--no-dev)",
        "chk_frozen": "Frozen (--frozen)",
        "chk_upgrade": "Upgrade (-U)",
        "lbl_cmd_run": "Comando (es. python main.py):",
        "chk_outdated": "Outdated",
        "lbl_pkg_pip_inst": "Pacchetto/i (separati da spazio):",
        "chk_req": "Requirements (-r)",
        "chk_system": "System",
        "lbl_pkg_pip_uninst": "Pacchetto/i:",
        "chk_json": "JSON",
        "lbl_pkg_pip_show": "Pacchetto:",
        "lbl_file_pip_comp": "File input (es. requirements.in):",
        "lbl_file_pip_sync": "File requirements.txt:",
        "lbl_ver_py_inst": "Versione (es. 3.12):",
        "chk_only_installed": "Solo installati",
        "chk_all_versions": "Tutte versioni",
        "lbl_ver_py_find": "Versione (opzionale):",
        "lbl_ver_py_pin": "Versione (es. 3.12):",
        "lbl_ver_py_uninst": "Versione:",
        "lbl_pkg_tool_inst": "Pacchetto (es. ruff):",
        "chk_force": "Force",
        "chk_show_paths": "Show paths",
        "lbl_tool_uninst": "Tool:",
        "lbl_cmd_tool_run": "Tool e argomenti (es. ruff check .):",
        "lbl_venv_name": "Nome (opzionale, default .venv):",
        "chk_seed": "Seed (--seed)",
        "chk_system_site": "System site",
        "chk_sdist": "Solo sdist",
        "chk_wheel": "Solo wheel",
        "lbl_publish_files": "File (opzionale, default dist/*):",
        "lbl_cache_clean_pkg": "Pacchetto (opz., vuoto=tutto):",
        "lbl_self_ver": "Versione (opz., vuoto=ultima):",
        
        # Error & Dialog messages
        "err_title": "Errore",
        "warn_title": "Attenzione",
        "info_title": "Info",
        "err_no_pkg": "Inserisci il nome del pacchetto",
        "err_no_pkgs": "Inserisci i pacchetti",
        "err_no_cmd": "Inserisci il comando da eseguire",
        "err_no_file": "Inserisci il file di input",
        "err_no_reqs": "Inserisci il file requirements.txt",
        "err_no_ver": "Inserisci la versione",
        "err_no_tool": "Inserisci il nome del tool",
        "err_no_tool_cmd": "Inserisci il comando",
        "warn_running": "Un comando è già in esecuzione.",
        "msg_stopped": "\nProcesso terminato dall'utente\n",
        "msg_no_process": "Nessun processo in esecuzione",
        "msg_uv_not_found": "UV non trovato",
        
        "msg_uv_not_found_win": (
            "Il comando 'uv' non è stato trovato nel PATH.\n\n"
            "Installalo con uno di questi metodi:\n\n"
            "METODO 1 - PowerShell (consigliato):\n"
            "powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"\n\n"
            "METODO 2 - winget:\n"
            "winget install --id=astral-sh.uv -e\n\n"
            "METODO 3 - pip:\n"
            "pip install uv\n\n"
            "Dopo l'installazione, RIAVVIA il terminale."
        ),
        "msg_uv_not_found_linux": (
            "Il comando 'uv' non è stato trovato nel PATH.\n\n"
            "Installalo con:\n"
            "curl -LsSf https://astral.sh/uv/install.sh | sh\n\n"
            "Poi riavvia il terminale o esegui:\n"
            "source $HOME/.local/bin/env"
        ),
        "msg_uv_not_found_err": "ERRORE: 'uv' non trovato. Installalo con:\n",
        "msg_uv_not_found_err_win_desc": (
            "   winget install --id=astral-sh.uv -e\n"
            "   oppure: pip install uv\n"
        ),
        "msg_uv_not_found_err_linux_desc": (
            "   curl -LsSf https://astral.sh/uv/install.sh | sh\n"
        ),
        
        "msg_about_text": (
            "UV Manager GUI\n\n"
            "Interfaccia grafica per il gestore di pacchetti uv\n"
            "Sviluppato con Python e Tkinter\n\n"
            "Compatibile con:\n"
            "• Linux (tutte le distribuzioni)\n"
            "• Windows 10/11\n\n"
            "Interfaccia adattiva per qualsiasi risoluzione\n\n"
            "Documentazione: https://docs.astral.sh/uv/\n"
            "Data: Giugno 2026"
        ),
        
        "console_execution": "\n============================================================\n>>> Esecuzione: {}\n",
        "console_directory": ">>> Directory: {}\n",
        "console_system": ">>> Sistema: {}\n",
        "console_exit_code": "\n>>> Processo terminato con codice: {}\n",
        "console_term_error": "Errore terminazione: {}\n",
        "console_error": "ERRORE: {}\n",
        "info_system_os": "[Info] Sistema operativo rilevato: {} {}",
        "info_system_py": "[Info] Python: {}",
        "layout_sash_pos": "[Layout] Sash posizionato a {}px",
        "layout_sash_err": "[Warning] Impossibile posizionare il sash: {}",

        # Help texts (Italian)
        "help_overview": """UV - GESTORE PACCHETTI PYTHON ULTRA-VELOCE

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
        "help_init": """UV INIT - Inizializza un nuovo progetto Python

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
        "help_add": """UV ADD - Aggiungi dipendenze al progetto

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
        "help_remove": """UV REMOVE - Rimuovi dipendenze dal progetto

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
        "help_sync": """UV SYNC - Sincronizza l'ambiente con il lockfile

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
        "help_lock": """UV LOCK - Aggiorna il lockfile senza installare

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
        "help_run": """UV RUN - Esegui comandi nell'ambiente del progetto

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
        "help_pip_install": """UV PIP INSTALL - Installa pacchetti (modalità pip)

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
        "help_pip_uninstall": """UV PIP UNINSTALL - Disinstalla pacchetti

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
        "help_pip_list": """UV PIP LIST - Elenca pacchetti installati

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
        "help_pip_freeze": """UV PIP FREEZE - Output in formato requirements.txt

SINTASSI: uv pip freeze [OPZIONI]

COSA FA:
Stampa i pacchetti installati nel formato usato da requirements.txt
(nome==versione). Compatibile con pip freeze.

ESEMPI:
  uv pip freeze                    # Output standard
  uv pip freeze > requirements.txt # Salva su file
  uv pip freeze --python 3.11      # Per specifico Python
""",
        "help_pip_show": """UV PIP SHOW - Mostra informazioni su un pacchetto

SINTASSI: uv pip show <PACCHETTO> [PACCHETTI...]

COSA FA:
Mostra informazioni dettagliate su uno o più pacchetti installati:
versione, percorso, dipendenze, metadata, ecc.

ESEMPI:
  uv pip show requests             # Info su requests
  uv pip show requests flask       # Info su più pacchetti
""",
        "help_pip_check": """UV PIP CHECK - Verifica compatibilità dipendenze

SINTASSI: uv pip check [OPZIONI]

COSA FA:
Verifica che tutte le dipendenze installate abbiano versioni compatibili
tra loro.

ESEMPI:
  uv pip check                     # Verifica ambiente corrente
  uv pip check --python 3.11       # Verifica per Python specifico
""",
        "help_pip_compile": """UV PIP COMPILE - Compila requirements.in in requirements.txt

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
        "help_pip_sync": """UV PIP SYNC - Sincronizza ambiente con requirements.txt

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
        "help_python_install": """UV PYTHON INSTALL - Installa versioni di Python

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
        "help_python_list": """UV PYTHON LIST - Elenca versioni Python disponibili

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
        "help_python_find": """UV PYTHON FIND - Trova un interprete Python

SINTASSI: uv python find [VERSIONE] [OPZIONI]

COSA FA:
Trova il percorso di un interprete Python disponibile.

ESEMPI:
  uv python find                 # Python default
  uv python find 3.12            # Python 3.12
  uv python find --system        # Solo Python di sistema
""",
        "help_python_pin": """UV PYTHON PIN - Fissa la versione Python del progetto

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
        "help_python_uninstall": """UV PYTHON UNINSTALL - Disinstalla versioni Python

SINTASSI: uv python uninstall <VERSIONI...> [OPZIONI]

COSA FA:
Rimuove versioni di Python installate tramite uv python install.

ESEMPI:
  uv python uninstall 3.11       # Disinstalla Python 3.11
  uv python uninstall 3.11 3.12  # Più versioni
  uv python uninstall --all      # Tutte le versioni gestite
""",
        "help_tool_install": """UV TOOL INSTALL - Installa tool CLI Python

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
        "help_tool_list": """UV TOOL LIST - Elenca i tool installati

SINTASSI: uv tool list [OPZIONI]

COSA FA:
Mostra tutti i tool installati tramite uv tool install.

ESEMPI:
  uv tool list                   # Lista completa
  uv tool list --show-paths      # Mostra percorsi executabili
  uv tool list --show-version-specifiers  # Mostra specifiche versione
""",
        "help_tool_uninstall": """UV TOOL UNINSTALL - Disinstalla un tool

SINTASSI: uv tool uninstall <TOOL> [TOOL...] [OPZIONI]

COSA FA:
Rimuove uno o più tool installati con uv tool install.

ESEMPI:
  uv tool uninstall ruff         # Disinstalla ruff
  uv tool uninstall ruff black   # Più tool
  uv tool uninstall --all        # Tutti i tool
""",
        "help_tool_run": """UV TOOL RUN (UVX) - Esegui tool senza installazione

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
        "help_venv": """UV VENV - Crea ambiente virtuale

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
        "help_build": """UV BUILD - Costruisci pacchetti distribuibili

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
        "help_publish": """UV PUBLISH - Pubblica pacchetti su PyPI

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
        "help_cache": """UV CACHE - Gestisci la cache di uv

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
        "help_self_update": """UV SELF UPDATE - Aggiorna uv stesso

SINTASSI: uv self update [VERSIONE] [OPZIONI]

COSA FA:
Aggiorna uv all'ultima versione o a una versione specifica.

ESEMPI:
  uv self update                 # Aggiorna all'ultima versione
  uv self update 0.5.0           # Aggiorna a versione specifica

OPZIONI:
  --force                Forza aggiornamento
""",
        "help_tree": """UV TREE - Mostra albero delle dipendenze

SINTASSI: uv tree [OPZIONI]

COSA FA:
Mostra l'albero delle dipendenze del progetto in formato visuale.

ESEMPI:
  uv tree                        # Albero completo
  uv tree --outdated             # Solo dipendenze con aggiornamenti
  uv tree --universal            # Per tutte le piattaforme
  uv tree --depth 2              # Limita profondità
""",
    },
    
    "en": {
        # UI Strings
        "title": "UV Manager - Complete Graphical Interface",
        "menu_file": "File",
        "menu_browse_dir": "Change working directory...",
        "menu_exit": "Exit",
        "menu_help": "Help",
        "menu_overview": "Overview of uv",
        "menu_proj_cmds": "Project Commands",
        "menu_pip_cmds": "Pip Commands",
        "menu_py_cmds": "Python Commands",
        "menu_tool_cmds": "Tool Commands",
        "menu_other_cmds": "Other Commands",
        "menu_official_doc": "Official documentation",
        "menu_about": "About",
        "menu_lang": "Language (Lingua)",
        "menu_lang_auto": "Auto Detect",
        "menu_lang_en": "English",
        "menu_lang_it": "Italiano",
        "msg_lang_changed": "Language changed",
        "msg_lang_restart": "Please restart the application to apply the new language.",
        
        # Labels and Frames
        "frame_working_dir": "Working Directory",
        "btn_browse": "Browse...",
        "frame_console_title": "Console Output (drag border to resize)",
        "btn_clear_console": "Clear Console",
        "btn_stop_process": "Stop process",
        "tab_project": "Project",
        "tab_pip": "Pip",
        "tab_python": "Python",
        "tab_tool": "Tool",
        "tab_build_publish": "Build/Publish",
        "tab_system": "System",
        "btn_execute": "Execute",
        "btn_close": "Close",
        
        # Command Section Titles
        "title_init": "uv init - Create project",
        "title_add": "uv add - Add dependency",
        "title_remove": "uv remove - Remove dependency",
        "title_sync": "uv sync - Sync environment",
        "title_lock": "uv lock - Update lockfile",
        "title_run": "uv run - Run command",
        "title_tree": "uv tree - Dependency tree",
        "title_pip_install": "uv pip install - Install packages",
        "title_pip_uninstall": "uv pip uninstall - Uninstall",
        "title_pip_list": "uv pip list - List packages",
        "title_pip_freeze": "uv pip freeze - Requirements output",
        "title_pip_show": "uv pip show - Package info",
        "title_pip_check": "uv pip check - Verify dependencies",
        "title_pip_compile": "uv pip compile - Compile requirements",
        "title_pip_sync": "uv pip sync - Sync with requirements",
        "title_python_install": "uv python install - Install Python",
        "title_python_list": "uv python list - List Python",
        "title_python_find": "uv python find - Find interpreter",
        "title_python_pin": "uv python pin - Pin project version",
        "title_python_uninstall": "uv python uninstall - Uninstall Python",
        "title_tool_install": "uv tool install - Install tool",
        "title_tool_list": "uv tool list - List tools",
        "title_tool_uninstall": "uv tool uninstall - Uninstall tool",
        "title_tool_run": "uv tool run (uvx) - Run tool",
        "title_venv": "uv venv - Create virtual environment",
        "title_build": "uv build - Build packages",
        "title_publish": "uv publish - Publish on PyPI",
        "title_cache_dir": "uv cache dir - Show cache path",
        "title_cache_clean": "uv cache clean - Clean cache",
        "title_cache_prune": "uv cache prune - Remove orphan entries",
        "title_self_update": "uv self update - Update uv",
        "title_cache": "uv cache - Cache management",
        
        # Form Fields & Flags
        "lbl_project_name": "Project name:",
        "chk_lib": "Lib (--lib)",
        "chk_app": "App (--app)",
        "chk_noreadme": "No README",
        "lbl_pkg_add": "Package (e.g. requests):",
        "chk_dev": "Dev (--dev)",
        "chk_editable": "Editable (-e)",
        "lbl_pkg_remove": "Package:",
        "chk_no_dev": "No dev (--no-dev)",
        "chk_frozen": "Frozen (--frozen)",
        "chk_upgrade": "Upgrade (-U)",
        "lbl_cmd_run": "Command (e.g. python main.py):",
        "chk_outdated": "Outdated",
        "lbl_pkg_pip_inst": "Package(s) (space separated):",
        "chk_req": "Requirements (-r)",
        "chk_system": "System",
        "lbl_pkg_pip_uninst": "Package(s):",
        "chk_json": "JSON",
        "lbl_pkg_pip_show": "Package:",
        "lbl_file_pip_comp": "Input file (e.g. requirements.in):",
        "lbl_file_pip_sync": "requirements.txt file:",
        "lbl_ver_py_inst": "Version (e.g. 3.12):",
        "chk_only_installed": "Only installed",
        "chk_all_versions": "All versions",
        "lbl_ver_py_find": "Version (optional):",
        "lbl_ver_py_pin": "Version (e.g. 3.12):",
        "lbl_ver_py_uninst": "Version:",
        "lbl_pkg_tool_inst": "Package (e.g. ruff):",
        "chk_force": "Force",
        "chk_show_paths": "Show paths",
        "lbl_tool_uninst": "Tool:",
        "lbl_cmd_tool_run": "Tool and arguments (e.g. ruff check .):",
        "lbl_venv_name": "Name (optional, default .venv):",
        "chk_seed": "Seed (--seed)",
        "chk_system_site": "System site",
        "chk_sdist": "Sdist only",
        "chk_wheel": "Wheel only",
        "lbl_publish_files": "Files (optional, default dist/*):",
        "lbl_cache_clean_pkg": "Package (opt., empty=all):",
        "lbl_self_ver": "Version (opt., empty=latest):",
        
        # Error & Dialog messages
        "err_title": "Error",
        "warn_title": "Warning",
        "info_title": "Info",
        "err_no_pkg": "Please enter package name",
        "err_no_pkgs": "Please enter packages",
        "err_no_cmd": "Please enter the command to run",
        "err_no_file": "Please enter the input file",
        "err_no_reqs": "Please enter the requirements.txt file",
        "err_no_ver": "Please enter version",
        "err_no_tool": "Please enter the tool name",
        "err_no_tool_cmd": "Please enter the command",
        "warn_running": "A command is already running.",
        "msg_stopped": "\nProcess stopped by user\n",
        "msg_no_process": "No process running",
        "msg_uv_not_found": "UV not found",
        
        "msg_uv_not_found_win": (
            "The 'uv' command was not found in your PATH.\n\n"
            "Install it using one of these methods:\n\n"
            "METHOD 1 - PowerShell (recommended):\n"
            "powershell -ExecutionPolicy ByPass -c \"irm https://astral.sh/uv/install.ps1 | iex\"\n\n"
            "METHOD 2 - winget:\n"
            "winget install --id=astral-sh.uv -e\n\n"
            "METHOD 3 - pip:\n"
            "pip install uv\n\n"
            "After installation, RESTART the terminal."
        ),
        "msg_uv_not_found_linux": (
            "The 'uv' command was not found in your PATH.\n\n"
            "Install it with:\n"
            "curl -LsSf https://astral.sh/uv/install.sh | sh\n\n"
            "Then restart the terminal or run:\n"
            "source $HOME/.local/bin/env"
        ),
        "msg_uv_not_found_err": "ERROR: 'uv' not found. Install it with:\n",
        "msg_uv_not_found_err_win_desc": (
            "   winget install --id=astral-sh.uv -e\n"
            "   or: pip install uv\n"
        ),
        "msg_uv_not_found_err_linux_desc": (
            "   curl -LsSf https://astral.sh/uv/install.sh | sh\n"
        ),
        
        "msg_about_text": (
            "UV Manager GUI\n\n"
            "Graphical user interface for the uv package manager\n"
            "Developed with Python and Tkinter\n\n"
            "Compatible with:\n"
            "• Linux (all distributions)\n"
            "• Windows 10/11\n\n"
            "Adaptive interface for any resolution\n\n"
            "Documentation: https://docs.astral.sh/uv/\n"
            "Date: June 2026"
        ),
        
        "console_execution": "\n============================================================\n>>> Execution: {}\n",
        "console_directory": ">>> Directory: {}\n",
        "console_system": ">>> System: {}\n",
        "console_exit_code": "\n>>> Process exited with code: {}\n",
        "console_term_error": "Termination error: {}\n",
        "console_error": "ERROR: {}\n",
        "info_system_os": "[Info] Detected OS: {} {}",
        "info_system_py": "[Info] Python: {}",
        "layout_sash_pos": "[Layout] Sash positioned at {}px",
        "layout_sash_err": "[Warning] Unable to position sash: {}",

        # Help texts (English)
        "help_overview": """UV - ULTRA-FAST PYTHON PACKAGE MANAGER

UV is a Python package and project manager written in Rust by Astral
(the creators of Ruff). It is extremely fast (10-100x faster than pip)
and replaces: pip, pip-tools, virtualenv, pyenv, poetry, pipx.

KEY FEATURES:
• Package resolution and installation in milliseconds
• Automatic virtual environment management
• Native support for pyproject.toml and uv.lock
• Multi-version Python management
• Global cache shared across projects
• Compatible with PyPI and private indexes

OFFICIAL WEBSITE: https://docs.astral.sh/uv/
""",
        "help_init": """UV INIT - Initialize a new Python project

SYNTAX: uv init [PROJECT_NAME] [OPTIONS]

WHAT IT DOES:
Creates a new project directory with the minimal necessary structure:
• pyproject.toml (project metadata and dependencies)
• README.md
• Example src/ folder or hello.py
• .python-version (optional)

EXAMPLES:
  uv init my_project           # Create project in my_project folder
  uv init --lib my_library     # Create library structure (with src/)
  uv init --app my_app          # Create application structure
  uv init --python 3.12          # Specify Python version

COMMON OPTIONS:
  --name NAME         Project name
  --package           Create as an installable package
  --lib               Library structure
  --app               Application structure (default)
  --python VERSION   Python version to use
  --no-readme         Do not create README.md
  --vcs git           Initialize with git (default)
  --no-vcs            Do not initialize git
""",
        "help_add": """UV ADD - Add dependencies to the project

SYNTAX: uv add <PACKAGE> [PACKAGES...] [OPTIONS]

WHAT IT DOES:
Adds one or more packages as project dependencies. Automatically updates
pyproject.toml and uv.lock, and installs the packages in the virtual environment.

EXAMPLES:
  uv add requests                    # Add requests
  uv add requests flask              # Add multiple packages
  uv add 'numpy>=1.26'              # With version constraint
  uv add --dev pytest               # As development dependency
  uv add --group docs sphinx        # In a specific group
  uv add --optional pdf reportlab   # As optional dependency
  uv add 'pkg[extra1,extra2]'       # With extras

COMMON OPTIONS:
  --dev, -d          Add as development dependency
  --group NAME       Add to a specific group
  --optional NAME    Add as optional dependency
  --editable, -e     Install in editable mode (for local development)
  --raw              Add without normalizing the specifier
  --frozen           Do not update uv.lock
  --no-sync          Do not sync the environment
""",
        "help_remove": """UV REMOVE - Remove dependencies from the project

SYNTAX: uv remove <PACKAGE> [PACKAGES...] [OPTIONS]

WHAT IT DOES:
Removes one or more packages from the project dependencies. Updates
pyproject.toml and uv.lock, and removes the packages from the virtual environment.

EXAMPLES:
  uv remove requests              # Remove requests
  uv remove requests flask        # Remove multiple packages
  uv remove --dev pytest          # Remove from dev dependencies
  uv remove --group docs sphinx   # Remove from a group

COMMON OPTIONS:
  --dev, -d          Remove from development dependencies
  --group NAME       Remove from a specific group
  --optional NAME    Remove from optional dependencies
  --frozen           Do not update uv.lock
  --no-sync          Do not sync the environment
""",
        "help_sync": """UV SYNC - Sync the environment with the lockfile

SYNTAX: uv sync [OPTIONS]

WHAT IT DOES:
Syncs the project's virtual environment with the dependencies specified
in pyproject.toml and uv.lock. Installs, updates, or removes packages
to make the environment match the lockfile exactly.

EXAMPLES:
  uv sync                     # Sync full environment
  uv sync --dev               # Include development dependencies
  uv sync --all-groups        # Include all groups
  uv sync --group test        # Only a specific group
  uv sync --no-dev            # Exclude dev dependencies
  uv sync --frozen            # Use existing lockfile, do not update it
  uv sync --inexact           # Remove packages not in the lockfile

COMMON OPTIONS:
  --dev, -d            Include development dependencies
  --no-dev             Exclude development dependencies
  --all-groups         Include all dependency groups
  --group NAME         Include a specific group
  --frozen             Do not update uv.lock
  --locked             Verify that uv.lock is up-to-date
  --inexact            Remove extra packages from environment
  --no-install-project Do not install the project itself
""",
        "help_lock": """UV LOCK - Update the lockfile without installing

SYNTAX: uv lock [OPTIONS]

WHAT IT DOES:
Updates the uv.lock file with resolved dependencies, but does NOT install
them in the virtual environment.

EXAMPLES:
  uv lock                    # Update uv.lock
  uv lock --upgrade          # Upgrade all dependencies
  uv lock --upgrade-package requests  # Upgrade only requests

COMMON OPTIONS:
  --upgrade, -U              Upgrade all dependencies
  --upgrade-package PKG      Upgrade only a specific package
  --locked                   Verify that the lockfile is up-to-date
  --check                    Verify without writing
""",
        "help_run": """UV RUN - Run commands in the project environment

SYNTAX: uv run [OPTIONS] <COMMAND> [ARGUMENTS...]

WHAT IT DOES:
Runs a command ensuring that the virtual environment is synced and available.
If the environment does not exist, it is created automatically.

EXAMPLES:
  uv run python main.py                # Run Python script
  uv run pytest                        # Run pytest
  uv run ruff check .                  # Run ruff
  uv run --with requests python -c "..."  # With temporary packages
  uv run --script script.py            # Run script with inline metadata

COMMON OPTIONS:
  --with PACKAGE         Add temporary packages to the execution
  --all-extras           Include all extras
  --extra NAME           Include a specific extra
  --no-sync              Do not sync before running
  --frozen               Do not update uv.lock
  --isolated             Use a temporary isolated environment
  --script               Run as PEP 723 script
""",
        "help_pip_install": """UV PIP INSTALL - Install packages (pip mode)

SYNTAX: uv pip install <PACKAGE> [OPTIONS]

WHAT IT DOES:
A pip-compatible mode to install packages in a virtual environment.
Useful when not using pyproject.toml.

DIFFERENCE WITH "uv add":
• uv add → modifies pyproject.toml (project management)
• uv pip install → installs directly (classic pip style)

EXAMPLES:
  uv pip install requests                     # Install package
  uv pip install -r requirements.txt          # From requirements file
  uv pip install -e .                         # Install current project
  uv pip install 'numpy>=1.26,<2.0'          # With constraints
  uv pip install --python 3.11 requests       # In Python 3.11 environment
  uv pip install --system requests            # In system environment

COMMON OPTIONS:
  -r, --requirement FILE   requirements.txt file
  -e, --editable           Install in editable mode
  --python VERSION        Target Python
  --system                 Install in system environment
  --prefix PATH            Install in a prefix path
  --upgrade, -U            Upgrade packages
  --reinstall              Reinstall all packages
  --no-deps                Do not install dependencies
""",
        "help_pip_uninstall": """UV PIP UNINSTALL - Uninstall packages

SYNTAX: uv pip uninstall <PACKAGE> [PACKAGES...] [OPTIONS]

WHAT IT DOES:
Removes packages from the current virtual environment.

EXAMPLES:
  uv pip uninstall requests              # Uninstall package
  uv pip uninstall requests flask        # Multiple packages
  uv pip uninstall -r requirements.txt   # From requirements file
  uv pip uninstall --system requests     # From system environment

OPTIONS:
  -r, --requirement FILE   File with package list
  --python VERSION        Target Python
  --system                 System environment
""",
        "help_pip_list": """UV PIP LIST - List installed packages

SYNTAX: uv pip list [OPTIONS]

WHAT IT DOES:
Shows all installed packages in the current virtual environment with their versions.

EXAMPLES:
  uv pip list                    # Complete list
  uv pip list --outdated         # Only outdated packages
  uv pip list --format json      # Output in JSON format
  uv pip list --editable         # Only editable packages

OPTIONS:
  --outdated             Show only packages with updates
  --editable             Only packages in editable mode
  --format FORMAT        Output: columns, freeze, json (default: columns)
  --python VERSION      Target Python
""",
        "help_pip_freeze": """UV PIP FREEZE - Output in requirements.txt format

SYNTAX: uv pip freeze [OPTIONS]

WHAT IT DOES:
Prints installed packages in the format used by requirements.txt (name==version).
Compatible with pip freeze.

EXAMPLES:
  uv pip freeze                    # Standard output
  uv pip freeze > requirements.txt # Save to file
  uv pip freeze --python 3.11      # For specific Python
""",
        "help_pip_show": """UV PIP SHOW - Show information about a package

SYNTAX: uv pip show <PACKAGE> [PACKAGES...]

WHAT IT DOES:
Shows detailed information about one or more installed packages:
version, path, dependencies, metadata, etc.

EXAMPLES:
  uv pip show requests             # Info on requests
  uv pip show requests flask       # Info on multiple packages
""",
        "help_pip_check": """UV PIP CHECK - Verify dependency compatibility

SYNTAX: uv pip check [OPTIONS]

WHAT IT DOES:
Verifies that all installed dependencies have mutually compatible versions.

EXAMPLES:
  uv pip check                     # Verify current environment
  uv pip check --python 3.11       # Verify for specific Python
""",
        "help_pip_compile": """UV PIP COMPILE - Compile requirements.in to requirements.txt

SYNTAX: uv pip compile requirements.in [OPTIONS]

WHAT IT DOES:
Resolves dependencies from a requirements.in file and generates a complete
requirements.txt with all transitive dependencies.

EXAMPLES:
  uv pip compile requirements.in                    # Compile
  uv pip compile requirements.in -o reqs.txt        # Specific output file
  uv pip compile requirements.in --upgrade          # Upgrade all
  uv pip compile pyproject.toml                     # From pyproject.toml

OPTIONS:
  -o, --output-file FILE   Output file name
  --upgrade, -U            Upgrade all dependencies
  --upgrade-package PKG    Upgrade specific package
  --universal              Generate for all platforms
  --python-version VER     Target Python version
""",
        "help_pip_sync": """UV PIP SYNC - Sync environment with requirements.txt

SYNTAX: uv pip sync requirements.txt [OPTIONS]

WHAT IT DOES:
Syncs the virtual environment with a requirements.txt file.

EXAMPLES:
  uv pip sync requirements.txt           # Sync
  uv pip sync requirements.txt --dry-run # Show what would be done
  uv pip sync req1.txt req2.txt          # Multiple files

OPTIONS:
  --dry-run              Show actions without executing them
  --python VERSION      Target Python
  --system               System environment
""",
        "help_python_install": """UV PYTHON INSTALL - Install Python versions

SYNTAX: uv python install [VERSIONS...] [OPTIONS]

WHAT IT DOES:
Downloads and installs standalone Python versions managed by uv.

EXAMPLES:
  uv python install                    # Install default version
  uv python install 3.12               # Install Python 3.12
  uv python install 3.11 3.12 3.13     # Multiple versions
  uv python install 3.12t              # Python 3.12 with free-threading
  uv python install cpython-3.12       # Specific implementation
  uv python install --preview 3.14     # Preview versions

OPTIONS:
  --mirror URL           Download mirror
  --force                Reinstall even if exists
  --clean                Remove temporary downloads
  --preview              Include preview versions
""",
        "help_python_list": """UV PYTHON LIST - List available Python versions

SYNTAX: uv python list [OPTIONS]

WHAT IT DOES:
Shows all available Python versions.

EXAMPLES:
  uv python list                 # All versions
  uv python list --only-installed  # Only installed versions
  uv python list --all-versions  # All available versions
  uv python list --all-architectures  # For all architectures
  uv python list --all-implementations  # CPython, PyPy, GraalPy

OPTIONS:
  --only-installed         Only installed versions
  --only-downloads         Only downloadable versions
  --all-versions           All available versions
  --all-architectures      All architectures
  --all-implementations    CPython, PyPy, GraalPy, etc.
  --all-platforms          All platforms
""",
        "help_python_find": """UV PYTHON FIND - Find a Python interpreter

SYNTAX: uv python find [VERSION] [OPTIONS]

WHAT IT DOES:
Finds the path of an available Python interpreter.

EXAMPLES:
  uv python find                 # Default Python
  uv python find 3.12            # Python 3.12
  uv python find --system        # Only system Python
""",
        "help_python_pin": """UV PYTHON PIN - Pin the project Python version

SYNTAX: uv python pin <VERSION> [OPTIONS]

WHAT IT DOES:
Creates or updates the .python-version file in the current directory.

EXAMPLES:
  uv python pin 3.12             # Pin to Python 3.12
  uv python pin 3.11 --global    # Pin globally
  uv python pin 3.12 --resolved  # Use full resolved version

OPTIONS:
  --global               Pin globally (not in project)
  --resolved             Use full resolved version
""",
        "help_python_uninstall": """UV PYTHON UNINSTALL - Uninstall Python versions

SYNTAX: uv python uninstall <VERSIONS...> [OPTIONS]

WHAT IT DOES:
Removes Python versions installed via uv python install.

EXAMPLES:
  uv python uninstall 3.11       # Uninstall Python 3.11
  uv python uninstall 3.11 3.12  # Multiple versions
  uv python uninstall --all      # All managed versions
""",
        "help_tool_install": """UV TOOL INSTALL - Install Python CLI tools

SYNTAX: uv tool install <PACKAGE> [OPTIONS]

WHAT IT DOES:
Installs a Python package as a global CLI tool in an isolated environment.
Similar to pipx.

EXAMPLES:
  uv tool install ruff           # Install ruff
  uv tool install black          # Install black
  uv tool install httpie         # Install httpie
  uv tool install --force ruff   # Reinstall
  uv tool install --python 3.12 ruff  # With specific Python

OPTIONS:
  --from PACKAGE       Package to install from
  --with PACKAGE       Add extra dependencies
  --python VERSION      Python to use
  --force                Overwrite existing installations
  --editable             Install in editable mode
""",
        "help_tool_list": """UV TOOL LIST - List installed tools

SYNTAX: uv tool list [OPTIONS]

WHAT IT DOES:
Shows all tools installed via uv tool install.

EXAMPLES:
  uv tool list                   # Complete list
  uv tool list --show-paths      # Show executable paths
  uv tool list --show-version-specifiers  # Show version specifiers
""",
        "help_tool_uninstall": """UV TOOL UNINSTALL - Uninstall a tool

SYNTAX: uv tool uninstall <TOOL> [TOOL...] [OPTIONS]

WHAT IT DOES:
Removes one or more tools installed with uv tool install.

EXAMPLES:
  uv tool uninstall ruff         # Uninstall ruff
  uv tool uninstall ruff black   # Multiple tools
  uv tool uninstall --all        # All tools
""",
        "help_tool_run": """UV TOOL RUN (UVX) - Run tools without installation

SYNTAX: uv tool run <TOOL> [ARGUMENTS...]
          uvx <TOOL> [ARGUMENTS...]

WHAT IT DOES:
Runs a Python tool in a temporary isolated environment.

EXAMPLES:
  uvx ruff check .               # Run ruff
  uvx black --check .            # Run black
  uvx cowsay "Hello!"            # Run cowsay
  uvx --from httpie http GET ... # Tool with different name
  uvx --with requests python -c "..."  # With extra dependencies

OPTIONS:
  --from PACKAGE       Package to run from
  --with PACKAGE       Add extra dependencies
  --python VERSION      Python to use
  --isolated             Do not use global cache
""",
        "help_venv": """UV VENV - Create virtual environment

SYNTAX: uv venv [PATH] [OPTIONS]

WHAT IT DOES:
Creates a Python virtual environment.

EXAMPLES:
  uv venv                        # Create .venv in current directory
  uv venv my_env                # Create my_env
  uv venv --python 3.12          # With specific Python
  uv venv --python 3.12 --seed   # With pip and setuptools
  uv venv --system-site-packages # Access to system site packages

OPTIONS:
  --python VERSION      Python version to use
  --seed                 Install pip, setuptools, wheel
  --system-site-packages # Access to system site packages
  --allow-existing       Do not fail if already exists
  --relocatable          Create relocatable environment
""",
        "help_build": """UV BUILD - Build distributable packages

SYNTAX: uv build [OPTIONS] [PATH]

WHAT IT DOES:
Builds distributable packages (sdist and wheel).

EXAMPLES:
  uv build                       # Build current project
  uv build --sdist               # sdist only
  uv build --wheel               # wheel only
  uv build --out-dir dist_custom # Custom output directory
  uv build ./another_project     # Build another project

OPTIONS:
  --package NAME         Specific package in workspace
  --all-packages         All packages in workspace
  --sdist                Source distribution only
  --wheel                Wheel only
  --out-dir DIR          Output directory
  --no-sources           Do not use alternative sources
""",
        "help_publish": """UV PUBLISH - Publish packages to PyPI

SYNTAX: uv publish [OPTIONS] [FILES...]

WHAT IT DOES:
Publishes packages (sdist/wheel) to an index like PyPI.

EXAMPLES:
  uv publish                   # Publish from dist/
  uv publish dist/*.whl        # Publish specific wheels
  uv publish --index testpypi  # To TestPyPI
  uv publish --token ...       # With authentication token

OPTIONS:
  --index NAME           Index name from pyproject.toml
  --publish-url URL      Index URL
  --token TOKEN          Authentication token
  --username USER        Username
  --password PASS        Password
  --check-url URL        Verify if version already exists
""",
        "help_cache": """UV CACHE - Manage uv cache

SYNTAX: uv cache <COMMAND> [OPTIONS]

AVAILABLE COMMANDS:
  uv cache directory       Show cache path
  uv cache clean           Clean cache
  uv cache prune           Remove unreferenced entries

EXAMPLES:
  uv cache dir                     # Where the cache is located
  uv cache clean                   # Clean entire cache
  uv cache clean requests          # Clean cache for a package
  uv cache prune                   # Remove orphan entries
""",
        "help_self_update": """UV SELF UPDATE - Update uv itself

SYNTAX: uv self update [VERSION] [OPTIONS]

WHAT IT DOES:
Updates uv to the latest version or to a specific version.

EXAMPLES:
  uv self update                 # Update to the latest version
  uv self update 0.5.0           # Update to specific version

OPTIONS:
  --force                Force update
""",
        "help_tree": """UV TREE - Show dependency tree

SYNTAX: uv tree [OPTIONS]

WHAT IT DOES:
Shows the project dependency tree in visual format.

EXAMPLES:
  uv tree                        # Complete tree
  uv tree --outdated             # Only dependencies with updates
  uv tree --universal            # For all platforms
  uv tree --depth 2              # Limit depth
""",
    }
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
        
        # Carica configurazione e rileva la lingua attiva
        self.config = load_config()
        self.lang_setting = self.config.get("language", "auto")
        if self.lang_setting == "auto":
            self.current_lang = detect_language()
        else:
            self.current_lang = self.lang_setting
            
        self.root.title(self.t("title"))
        
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
        
    def t(self, key):
        """Restituisce la traduzione per la lingua attiva"""
        return TRANSLATIONS[self.current_lang].get(key, TRANSLATIONS["en"].get(key, key))
        
    def _change_language(self):
        """Gestisce la variazione manuale della lingua"""
        new_lang = self.lang_var.get()
        self.config["language"] = new_lang
        save_config(self.config)
        messagebox.showinfo(
            self.t("msg_lang_changed"),
            self.t("msg_lang_restart")
        )
    
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
                print(self.t("layout_sash_pos").format(sash_position))
        except Exception as e:
            print(self.t("layout_sash_err").format(e))
    
    def _check_uv_installed(self):
        """Verifica che uv sia installato - MESSAGGIO CROSS PLATFORM"""
        if not shutil.which("uv"):
            if IS_WINDOWS:
                install_msg = self.t("msg_uv_not_found_win")
            else:
                install_msg = self.t("msg_uv_not_found_linux")
            
            self.root.after(100, lambda: messagebox.showwarning(
                self.t("msg_uv_not_found"), install_msg
            ))
    
    def _build_menu(self):
        """Crea la barra dei menu con Aiuto dettagliato"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=self.t("menu_browse_dir"), command=self._browse_dir)
        
        # Sottomenu Lingua
        lang_menu = tk.Menu(file_menu, tearoff=0)
        self.lang_var = tk.StringVar(value=self.lang_setting)
        lang_menu.add_radiobutton(label=self.t("menu_lang_auto"), variable=self.lang_var, value="auto", command=self._change_language)
        lang_menu.add_radiobutton(label=self.t("menu_lang_en"), variable=self.lang_var, value="en", command=self._change_language)
        lang_menu.add_radiobutton(label=self.t("menu_lang_it"), variable=self.lang_var, value="it", command=self._change_language)
        file_menu.add_cascade(label=self.t("menu_lang"), menu=lang_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label=self.t("menu_exit"), command=self.root.quit)
        menubar.add_cascade(label=self.t("menu_file"), menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=self.t("menu_overview"), 
                              command=lambda: self._show_help(self.t("menu_overview"), TRANSLATIONS[self.current_lang]["help_overview"]))
        help_menu.add_separator()

        project_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title_key in [
            ("init", "title_init"),
            ("add", "title_add"),
            ("remove", "title_remove"),
            ("sync", "title_sync"),
            ("lock", "title_lock"),
            ("run", "title_run"),
            ("tree", "title_tree"),
        ]:
            project_menu.add_command(label=self.t(title_key), 
                                     command=lambda c=cmd, tk=title_key: self._show_help(self.t(tk), TRANSLATIONS[self.current_lang]["help_" + c]))
        help_menu.add_cascade(label=self.t("menu_proj_cmds"), menu=project_menu)

        pip_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title_key in [
            ("pip_install", "title_pip_install"),
            ("pip_uninstall", "title_pip_uninstall"),
            ("pip_list", "title_pip_list"),
            ("pip_freeze", "title_pip_freeze"),
            ("pip_show", "title_pip_show"),
            ("pip_check", "title_pip_check"),
            ("pip_compile", "title_pip_compile"),
            ("pip_sync", "title_pip_sync"),
        ]:
            pip_menu.add_command(label=self.t(title_key), 
                                 command=lambda c=cmd, tk=title_key: self._show_help(self.t(tk), TRANSLATIONS[self.current_lang]["help_" + c]))
        help_menu.add_cascade(label=self.t("menu_pip_cmds"), menu=pip_menu)

        python_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title_key in [
            ("python_install", "title_python_install"),
            ("python_list", "title_python_list"),
            ("python_find", "title_python_find"),
            ("python_pin", "title_python_pin"),
            ("python_uninstall", "title_python_uninstall"),
        ]:
            python_menu.add_command(label=self.t(title_key), 
                                    command=lambda c=cmd, tk=title_key: self._show_help(self.t(tk), TRANSLATIONS[self.current_lang]["help_" + c]))
        help_menu.add_cascade(label=self.t("menu_py_cmds"), menu=python_menu)

        tool_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title_key in [
            ("tool_install", "title_tool_install"),
            ("tool_list", "title_tool_list"),
            ("tool_uninstall", "title_tool_uninstall"),
            ("tool_run", "title_tool_run"),
        ]:
            tool_menu.add_command(label=self.t(title_key), 
                                  command=lambda c=cmd, tk=title_key: self._show_help(self.t(tk), TRANSLATIONS[self.current_lang]["help_" + c]))
        help_menu.add_cascade(label=self.t("menu_tool_cmds"), menu=tool_menu)

        other_menu = tk.Menu(help_menu, tearoff=0)
        for cmd, title_key in [
            ("venv", "title_venv"),
            ("build", "title_build"),
            ("publish", "title_publish"),
            ("cache", "title_cache"),
            ("self_update", "title_self_update"),
        ]:
            other_menu.add_command(label=self.t(title_key), 
                                   command=lambda c=cmd, tk=title_key: self._show_help(self.t(tk), TRANSLATIONS[self.current_lang]["help_" + c]))
        help_menu.add_cascade(label=self.t("menu_other_cmds"), menu=other_menu)

        help_menu.add_separator()
        help_menu.add_command(label=self.t("menu_official_doc"), 
                              command=lambda: webbrowser.open("https://docs.astral.sh/uv/"))
        help_menu.add_command(label=self.t("menu_about"), command=self._show_about)
        menubar.add_cascade(label=self.t("menu_help"), menu=help_menu)
    
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
        
        ttk.Button(help_win, text=self.t("btn_close"), command=help_win.destroy).pack(pady=5)
    
    def _show_about(self):
        messagebox.showinfo(
            self.t("menu_about"),
            self.t("msg_about_text")
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

        dir_frame = ttk.LabelFrame(top_frame, text=self.t("frame_working_dir"), padding=8)
        dir_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Entry(dir_frame, textvariable=self.working_dir).pack(
            side="left", padx=5, fill="x", expand=True
        )
        ttk.Button(dir_frame, text=self.t("btn_browse"), command=self._browse_dir).pack(side="left", padx=5)

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
                                        text=self.t("frame_console_title"), 
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
        ttk.Button(btn_frame, text=self.t("btn_clear_console"), 
                   command=self._clear_console).pack(side="left", padx=5)
        ttk.Button(btn_frame, text=self.t("btn_stop_process"), 
                   command=self._stop_process).pack(side="left", padx=5)
    
    def _build_project_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text=self.t("tab_project"))
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, self.t("title_init"), 
                                  [(self.t("lbl_project_name"), "init_name")],
                                  "init", row=0,
                                  extra_flags=[(self.t("chk_lib"), "init_lib"), 
                                               (self.t("chk_app"), "init_app"),
                                               (self.t("chk_noreadme"), "init_noreadme")])
        
        self._add_command_section(content, self.t("title_add"),
                                  [(self.t("lbl_pkg_add"), "add_pkg")],
                                  "add", row=1,
                                  extra_flags=[(self.t("chk_dev"), "add_dev"),
                                               (self.t("chk_editable"), "add_editable")])

        self._add_command_section(content, self.t("title_remove"),
                                  [(self.t("lbl_pkg_remove"), "remove_pkg")],
                                  "remove", row=2)

        self._add_command_section(content, self.t("title_sync"),
                                  [], "sync", row=3,
                                  extra_flags=[(self.t("chk_dev"), "sync_dev"),
                                               (self.t("chk_no_dev"), "sync_nodev"),
                                               (self.t("chk_frozen"), "sync_frozen")])

        self._add_command_section(content, self.t("title_lock"),
                                  [], "lock", row=4,
                                  extra_flags=[(self.t("chk_upgrade"), "lock_upgrade")])

        self._add_command_section(content, self.t("title_run"),
                                  [(self.t("lbl_cmd_run"), "run_cmd")],
                                  "run", row=5)

        self._add_command_section(content, self.t("title_tree"),
                                  [], "tree", row=6,
                                  extra_flags=[(self.t("chk_outdated"), "tree_outdated")])
    
    def _build_pip_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text=self.t("tab_pip"))
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, self.t("title_pip_install"),
                                  [(self.t("lbl_pkg_pip_inst"), "pip_inst_pkg")],
                                  "pip_install", row=0,
                                  extra_flags=[(self.t("chk_req"), "pip_inst_req"),
                                               (self.t("chk_editable"), "pip_inst_edit"),
                                               (self.t("chk_upgrade"), "pip_inst_upgrade"),
                                               (self.t("chk_system"), "pip_inst_system")])

        self._add_command_section(content, self.t("title_pip_uninstall"),
                                  [(self.t("lbl_pkg_pip_uninst"), "pip_uninst_pkg")],
                                  "pip_uninstall", row=1)

        self._add_command_section(content, self.t("title_pip_list"),
                                  [], "pip_list", row=2,
                                  extra_flags=[(self.t("chk_outdated"), "pip_list_outdated"),
                                               (self.t("chk_json"), "pip_list_json")])

        self._add_command_section(content, self.t("title_pip_freeze"),
                                  [], "pip_freeze", row=3)

        self._add_command_section(content, self.t("title_pip_show"),
                                  [(self.t("lbl_pkg_pip_show"), "pip_show_pkg")],
                                  "pip_show", row=4)

        self._add_command_section(content, self.t("title_pip_check"),
                                  [], "pip_check", row=5)

        self._add_command_section(content, self.t("title_pip_compile"),
                                  [(self.t("lbl_file_pip_comp"), "pip_comp_in")],
                                  "pip_compile", row=6,
                                  extra_flags=[(self.t("chk_upgrade"), "pip_comp_upgrade")])

        self._add_command_section(content, self.t("title_pip_sync"),
                                  [(self.t("lbl_file_pip_sync"), "pip_sync_file")],
                                  "pip_sync", row=7)
    
    def _build_python_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text=self.t("tab_python"))
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, self.t("title_python_install"),
                                  [(self.t("lbl_ver_py_inst"), "py_inst_ver")],
                                  "python_install", row=0)

        self._add_command_section(content, self.t("title_python_list"),
                                  [], "python_list", row=1,
                                  extra_flags=[(self.t("chk_only_installed"), "py_list_installed"),
                                               (self.t("chk_all_versions"), "py_list_all")])

        self._add_command_section(content, self.t("title_python_find"),
                                  [(self.t("lbl_ver_py_find"), "py_find_ver")],
                                  "python_find", row=2)

        self._add_command_section(content, self.t("title_python_pin"),
                                  [(self.t("lbl_ver_py_pin"), "py_pin_ver")],
                                  "python_pin", row=3)

        self._add_command_section(content, self.t("title_python_uninstall"),
                                  [(self.t("lbl_ver_py_uninst"), "py_uninst_ver")],
                                  "python_uninstall", row=4)
    
    def _build_tool_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text=self.t("tab_tool"))
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, self.t("title_tool_install"),
                                  [(self.t("lbl_pkg_tool_inst"), "tool_inst_pkg")],
                                  "tool_install", row=0,
                                  extra_flags=[(self.t("chk_force"), "tool_inst_force")])

        self._add_command_section(content, self.t("title_tool_list"),
                                  [], "tool_list", row=1,
                                  extra_flags=[(self.t("chk_show_paths"), "tool_list_paths")])

        self._add_command_section(content, self.t("title_tool_uninstall"),
                                  [(self.t("lbl_tool_uninst"), "tool_uninst_name")],
                                  "tool_uninstall", row=2)

        self._add_command_section(content, self.t("title_tool_run"),
                                  [(self.t("lbl_cmd_tool_run"), "tool_run_cmd")],
                                  "tool_run", row=3)
    
    def _build_build_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text=self.t("tab_build_publish"))
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, self.t("title_venv"),
                                  [(self.t("lbl_venv_name"), "venv_name")],
                                  "venv", row=0,
                                  extra_flags=[(self.t("chk_seed"), "venv_seed"),
                                               (self.t("chk_system_site"), "venv_sys")])

        self._add_command_section(content, self.t("title_build"),
                                  [], "build", row=1,
                                  extra_flags=[(self.t("chk_sdist"), "build_sdist"),
                                               (self.t("chk_wheel"), "build_wheel")])

        self._add_command_section(content, self.t("title_publish"),
                                  [(self.t("lbl_publish_files"), "publish_files")],
                                  "publish", row=2)
    
    def _build_system_tab(self):
        tab = ScrollableTab(self.notebook)
        self.notebook.add(tab, text=self.t("tab_system"))
        content = tab.inner_frame
        content.columnconfigure(0, weight=1)

        self._add_command_section(content, self.t("title_cache_dir"),
                                  [], "cache_dir", row=0)

        self._add_command_section(content, self.t("title_cache_clean"),
                                  [(self.t("lbl_cache_clean_pkg"), "cache_clean_pkg")],
                                  "cache_clean", row=1)

        self._add_command_section(content, self.t("title_cache_prune"),
                                  [], "cache_prune", row=2)

        self._add_command_section(content, self.t("title_self_update"),
                                  [(self.t("lbl_self_ver"), "self_ver")],
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
            input_frame, text=self.t("btn_execute"), width=12,
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
                messagebox.showerror(self.t("err_title"), self.t("err_no_pkg"))
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
                messagebox.showerror(self.t("err_title"), self.t("err_no_pkg"))
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
                messagebox.showerror(self.t("err_title"), self.t("err_no_cmd"))
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
                    messagebox.showerror(self.t("err_title"), self.t("err_no_pkgs"))
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
                messagebox.showerror(self.t("err_title"), self.t("err_no_pkgs"))
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
                messagebox.showerror(self.t("err_title"), self.t("err_no_pkg"))
                return
            cmd.extend(pkg.split())
        
        elif cmd_key == "pip_check":
            cmd.extend(["pip", "check"])
        
        elif cmd_key == "pip_compile":
            cmd.extend(["pip", "compile"])
            f = vars_dict["pip_comp_in"].get().strip()
            if not f:
                messagebox.showerror(self.t("err_title"), self.t("err_no_file"))
                return
            cmd.append(f)
            if flag_vars.get("pip_comp_upgrade", tk.BooleanVar()).get():
                cmd.append("--upgrade")
        
        elif cmd_key == "pip_sync":
            cmd.extend(["pip", "sync"])
            f = vars_dict["pip_sync_file"].get().strip()
            if not f:
                messagebox.showerror(self.t("err_title"), self.t("err_no_reqs"))
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
                messagebox.showerror(self.t("err_title"), self.t("err_no_ver"))
                return
            cmd.append(ver)
        
        elif cmd_key == "python_uninstall":
            cmd.extend(["python", "uninstall"])
            ver = vars_dict["py_uninst_ver"].get().strip()
            if not ver:
                messagebox.showerror(self.t("err_title"), self.t("err_no_ver"))
                return
            cmd.extend(ver.split())
        
        elif cmd_key == "tool_install":
            cmd.extend(["tool", "install"])
            pkg = vars_dict["tool_inst_pkg"].get().strip()
            if not pkg:
                messagebox.showerror(self.t("err_title"), self.t("err_no_pkg"))
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
                messagebox.showerror(self.t("err_title"), self.t("err_no_tool"))
                return
            cmd.extend(name.split())
        
        elif cmd_key == "tool_run":
            cmd.extend(["tool", "run"])
            run_cmd = vars_dict["tool_run_cmd"].get().strip()
            if not run_cmd:
                messagebox.showerror(self.t("err_title"), self.t("err_no_tool_cmd"))
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
        
        self._log(self.t("console_execution").format(" ".join(cmd)))
        self._log(self.t("console_directory").format(self.working_dir.get()))
        self._log(self.t("console_system").format("Windows" if IS_WINDOWS else "Linux"))
        self._log(f"{'='*60}\n")
        
        self._run_command(cmd)
    
    def _run_command(self, cmd):
        """Esegue il comando in un thread separato - CROSS PLATFORM"""
        if self.thread and self.thread.is_alive():
            messagebox.showwarning(self.t("warn_title"), self.t("warn_running"))
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
                self._log(self.t("console_exit_code").format(process.returncode))
                self.current_process = None
            except FileNotFoundError:
                if IS_WINDOWS:
                    self._log(self.t("msg_uv_not_found_err"))
                    self._log(self.t("msg_uv_not_found_err_win_desc"))
                else:
                    self._log(self.t("msg_uv_not_found_err"))
                    self._log(self.t("msg_uv_not_found_err_linux_desc"))
                self.current_process = None
            except Exception as e:
                self._log(self.t("console_error").format(str(e)))
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
                self._log(self.t("msg_stopped"))
            except Exception as e:
                self._log(self.t("console_term_error").format(e))
        else:
            messagebox.showinfo(self.t("info_title"), self.t("msg_no_process"))
    
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
    
    # Rilevamento lingua iniziale per stampe console di avvio
    config = load_config()
    lang_setting = config.get("language", "auto")
    start_lang = detect_language() if lang_setting == "auto" else lang_setting
    
    os_info = TRANSLATIONS[start_lang].get("info_system_os", TRANSLATIONS["en"]["info_system_os"])
    py_info = TRANSLATIONS[start_lang].get("info_system_py", TRANSLATIONS["en"]["info_system_py"])
    
    print(os_info.format(platform.system(), platform.release()))
    print(py_info.format(sys.version))
    
    app = UvManagerApp(root)
    root.mainloop()