import streamlit as st
import subprocess
import re
import os
from dotenv import load_dotenv
from pathlib import Path
import sys

# Setze UTF-8 Encoding für die gesamte Anwendung
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Konfiguriere sys.stdout und sys.stderr für UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Lade Umgebungsvariablen
load_dotenv()

st.set_page_config(
    page_title="Open Duck Research",
    page_icon="🦆",
    layout="wide"
)

# Default values from original configuration
DEFAULT_MAX_STEPS = 20  # from text_webbrowser_agent
DEFAULT_VERBOSITY = 2   # both agents use this
DEFAULT_PLANNING_INTERVAL = 4  # both agents use this
DEFAULT_TEXT_LIMIT = 100000  # from main()
DEFAULT_REASONING_EFFORT = "high"  # from LiteLLMModel
DEFAULT_MAX_COMPLETION_TOKENS = 8192  # from LiteLLMModel

# Seitenleiste mit Einstellungen
with st.sidebar:
    st.markdown("## ⚙️ Einstellungen")
    
    with st.expander("🤖 OpenAI Einstellungen", expanded=True):
        st.markdown("Konfiguriere das OpenAI LLM und die API-Parameter:")

        model = st.selectbox(
            'OpenAI Modell',
            options=['gpt-4.1-mini', 'gpt-4.1', 'gpt-4o-mini', 'gpt-4o'],
            index=0,
            help='Wähle das OpenAI Modell. gpt-4.1-mini ist der Standard und für die meisten Aufgaben optimal.'
        )
        
        api_key = st.text_input(
            'OpenAI API Key',
            value=os.getenv('OPENAI_API_KEY', ''),
            type='password',
            help='Dein OpenAI API Key. Kann aus der Umgebungsvariable OPENAI_API_KEY geladen oder manuell eingegeben werden.'
        )
        
        if not api_key:
            st.warning("⚠️ Bitte gib deinen OpenAI API Key ein, um die Recherche zu starten.")
            st.info("💡 Du kannst deinen API Key bei [OpenAI](https://platform.openai.com/api-keys) erstellen.")

        # HuggingFace Token
        hf_token = st.text_input(
            'HuggingFace Token',
            value=os.getenv('HF_TOKEN', ''),
            type='password',
            help='HuggingFace Token aus Umgebungsvariable HF_TOKEN oder manuell eingeben.'
        )

        max_completion_tokens = st.number_input(
            'Max. Completion Tokens',
            min_value=1000,
            max_value=32000,
            value=16000,
            help='Maximale Anzahl der Tokens für die Modell-Antwort. Standard: 16.000 Tokens'
        )
    
    with st.expander("🔍 Recherche Einstellungen", expanded=False):
        st.markdown("Passe die Parameter für die Web-Recherche an:")
        
        reasoning_effort = st.select_slider(
            'Überlegungsaufwand',
            options=['Schnell', 'Ausgewogen', 'Gründlich'],
            value='Gründlich',
            help='Bestimmt, wie sorgfältig der Agent seine Entscheidungen trifft. Standard: Gründlich (high)'
        )
        # Convert reasoning_effort text to API values
        reasoning_effort = {'Schnell': 'low', 'Ausgewogen': 'medium', 'Gründlich': 'high'}[reasoning_effort]
        
        max_steps = st.number_input(
            'Max. Anzahl der Schritte pro Agent-Ausführung', 
            min_value=1, max_value=100, 
            value=DEFAULT_MAX_STEPS,
            help='Maximale Anzahl der Einzelschritte, die ein Agent pro Recherche-Runde ausführen darf (z.B. Suche + 10x Seitenbesuch = 11 Schritte). Standard: 20 Schritte'
        )
        
        verbosity = st.selectbox(
            'Detailgrad der Ausgabe', 
            options=[0, 1, 2], 
            index=1,
            help='Wie detailliert sollen die internen Agent-Logs sein? 0=nur Ergebnisse, 1=normale Details, 2=alle Debug-Infos. Beeinflusst NICHT die Qualität des finalen Reports!'
        )
        
        planning_interval = st.number_input(
            'Planungsintervall', 
            min_value=1, max_value=20, 
            value=DEFAULT_PLANNING_INTERVAL,
            help='Nach wie vielen Einzelschritten soll der Agent seine Recherche-Strategie überdenken und anpassen? Niedrigere Werte = flexibler, höhere Werte = effizienter. Standard: 3 Schritte'
        )
        
        text_limit = st.number_input(
            'Textlimit pro Quelle', 
            min_value=1000, max_value=500000, 
            value=DEFAULT_TEXT_LIMIT,
            help='Maximale Anzahl der Zeichen, die pro Quelle verarbeitet werden. Standard: 100.000 Zeichen'
        )

    with st.expander("🔍 DuckDuckGo Einstellungen", expanded=False):
        st.markdown("Konfiguriere die DuckDuckGo-Suche:")
        
        max_results = st.number_input(
            'Maximale Anzahl Suchergebnisse',
            min_value=1,
            max_value=100,
            value=10,
            help='Wie viele Suchergebnisse sollen maximal abgerufen werden?'
        )
        
        region = st.selectbox(
            'Region',
            options=['de-de', 'us-en', 'uk-en', 'wt-wt'],
            index=0,
            help='Welche Region soll für die Suche verwendet werden?'
        )
        
        safesearch = st.selectbox(
            'SafeSearch',
            options=['on', 'moderate', 'off'],
            index=1,
            help='Welche SafeSearch-Einstellung soll verwendet werden?'
        )
        
        use_proxy = st.checkbox(
            '🌐 Proxies verwenden (deutsche + internationale)',
            value=True,
            help='Aktiviert die Nutzung von Proxy-Servern für anonymere Recherche. Kann die Geschwindigkeit reduzieren, aber Geo-Blocking umgehen. Standard: Aktiviert für bessere Anonymität.'
        )
        
        st.markdown("---")
        st.markdown("**🔄 Recherche-Runden Konfiguration**")
        
        max_search_rounds = st.slider(
            'Maximale Recherche-Runden',
            min_value=3,
            max_value=10,
            value=5,
            help='Anzahl der Such-Runden. Jede Runde = 1x DuckDuckGo Suche + Besuch von bis zu 10 Seiten. Mehr Runden = umfassendere aber langsamere Recherche.'
        )

# Hauptbereich
st.title('🦆 Open Duck Research')

st.markdown("""
### Willkommen bei Open Duck Research!

Diese App ermöglicht es dir, fundierte Multi-Runden-Recherchen im Internet durchzuführen und komplexe Berichte zu einem Thema zu erstellen.
Hierfür wird die DuckDuckGo Internetsuche mit intelligenter Suchstrategie verwendet. Gib bitte links Deinen LLM-Key ein und starte direkt mit der ersten Abfrage!

Die KI-Agenten werden:
- 🧠 Strategische Recherche-Runden planen
- 🔍 Multi-Runden Internetsuche durchführen
- 🌐 Verschiedene Quellen und Perspektiven erkunden
- 📝 Einen umfassenden, strukturierten Report erstellen

---
""")

# Eingabeformular
with st.form('input_form', clear_on_submit=False):
    st.markdown("### 🤔 Was möchtest du wissen?")
    question = st.text_area(
        'Deine Frage',
        placeholder='Stelle eine konkrete Frage, z.B.: "Welche Vor- und Nachteile haben Open Educational Resources für Lehrende?"',
        help='Je präziser die Frage, desto besser kann der Agent recherchieren.',
        height=100
    )
    
    submitted = st.form_submit_button('🚀 Recherche starten')

def extract_final_answer(output: str) -> str:
    """Extract the final answer from the output."""
    if "Got this answer:" in output:
        return output.split("Got this answer:")[-1].strip()
    return output.strip()


def format_status_message(message: str) -> str:
    """Format status message for better readability."""
    # Remove ANSI color codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    message = ansi_escape.sub('', message)
    
    # Übersetze englische Begriffe
    message = message.replace("Step ", "Schritt ")
    message = message.replace("Duration", "Dauer")
    message = message.replace("New run", "Neuer Durchlauf")
    message = message.replace("Error", "Fehler")
    message = message.replace("Got this answer:", "Erhaltene Antwort:")
    
    # Format step headers
    if "Schritt" in message and "Dauer" in message:
        return f" {message}"
    elif "Neuer Durchlauf" in message:
        return f" {message}"
    elif "Fehler" in message or "error" in message:
        return f" {message}"
    return message


def safe_unicode_convert(text):
    """Konvertiert Text sicher zu Unicode und behandelt Encoding-Probleme."""
    if text is None:
        return ""
    
    try:
        # Konvertiere zu String falls nötig
        text_str = str(text) if not isinstance(text, str) else text
        
        # Ersetze problematische Unicode-Zeichen durch sichere Alternativen
        # Ligaturen und spezielle Zeichen
        replacements = {
            '\ufb00': 'ff',  # ff Ligatur
            '\ufb01': 'fi',  # fi Ligatur
            '\ufb02': 'fl',  # fl Ligatur
            '\ufb03': 'ffi', # ffi Ligatur
            '\ufb04': 'ffl', # ffl Ligatur
            '\u2013': '-',   # En dash
            '\u2014': '--',  # Em dash
            '\u2018': "'",   # Left single quotation mark
            '\u2019': "'",   # Right single quotation mark
            '\u201c': '"',   # Left double quotation mark
            '\u201d': '"',   # Right double quotation mark
            '\u2026': '...', # Horizontal ellipsis
        }
        
        # Ersetze bekannte problematische Zeichen
        for old, new in replacements.items():
            text_str = text_str.replace(old, new)
        
        # Versuche UTF-8 Encoding mit Ersetzung
        safe_text = text_str.encode('utf-8', errors='replace').decode('utf-8')
        return safe_text
        
    except Exception as e:
        # Fallback: Entferne alle nicht-ASCII Zeichen
        try:
            return str(text).encode('ascii', errors='ignore').decode('ascii')
        except:
            return f"[Encoding-Fehler: {str(e)[:50]}]"


def run_research_query(model: str, question: str, max_steps: int, verbosity: int, planning_interval: int, 
               text_limit: int, reasoning_effort: str, max_completion_tokens: int,
               ddg_max_results: int, ddg_region: str, ddg_safesearch: str, use_proxy: bool = False,
               max_search_rounds: int = 5, api_key: str = '', hf_token: str = '',
               status_callback=None):
    import threading
    import litellm
    from dotenv import load_dotenv
    from huggingface_hub import login
    from scripts.text_inspector_tool import TextInspectorTool
    from scripts.text_web_browser import (
        ArchiveSearchTool,
        FinderTool,
        FindNextTool,
        PageDownTool,
        PageUpTool,
        SearchInformationTool,
        SimpleTextBrowser,
        VisitTool,
    )
    from scripts.visual_qa import visualizer
    from scripts.proxy_manager import ProxyManager
    from smolagents import (
        CodeAgent,
        LiteLLMModel,
        ToolCallingAgent,
    )
    import os

    # Progress callback helper - definiere zuerst!
    def progress(msg):
        if status_callback:
            status_callback(msg)
    
    # Set environment for compatibility
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    # Configure OpenAI API settings
    os.environ["OPENAI_API_BASE"] = 'https://api.openai.com/v1'
    os.environ["OPENAI_API_KEY"] = api_key or ''
    progress(f"🤖 OpenAI konfiguriert - Modell: {model}")
    
    os.environ["HF_TOKEN"] = hf_token or ''
    load_dotenv(override=True)
    
    # HuggingFace Login nur wenn Token vorhanden
    if hf_token:
        try:
            login(hf_token)
            progress("🤗 HuggingFace Login erfolgreich")
        except Exception as e:
            progress(f"⚠️ HuggingFace Login fehlgeschlagen: {str(e)[:50]}")
    
    # Detaillierte Callback-Funktionen für Agent-Schritte
    def create_step_callback(agent_name: str):
        """Erstellt eine Callback-Funktion für einen spezifischen Agent"""
        def step_callback(step, agent=None):
            try:
                from smolagents.memory import ActionStep, PlanningStep, FinalAnswerStep
                
                # Sichere Attribut-Prüfung für step_number
                step_num = getattr(step, 'step_number', '?')
                
                if isinstance(step, PlanningStep):
                    progress(f"🧠 {agent_name} - Schritt {step_num}: Planung wird erstellt...")
                    # Sichere Prüfung für Plan-Attribut
                    plan_content = getattr(step, 'plan', None)
                    if plan_content and isinstance(plan_content, str):
                        plan_preview = plan_content[:100] + "..." if len(plan_content) > 100 else plan_content
                        progress(f"📋 {agent_name} - Plan: {plan_preview}")
                
                elif isinstance(step, ActionStep):
                    action = getattr(step, 'action', None)
                    if action and isinstance(action, dict):
                        action_type = action.get('tool_name', 'Unbekannte Aktion')
                        progress(f"⚡ {agent_name} - Schritt {step_num}: Führe {action_type} aus...")
                        
                        # Spezifische Meldungen für verschiedene Tools
                        action_lower = action_type.lower()
                        if 'search' in action_lower:
                            progress(f"🔍 {agent_name} - Durchsuche das Internet...")
                        elif 'visit' in action_lower or 'page' in action_lower:
                            progress(f"🌐 {agent_name} - Besuche Webseite...")
                        elif 'inspect' in action_lower:
                            progress(f"📄 {agent_name} - Analysiere Dokument...")
                        elif 'find' in action_lower:
                            progress(f"🔎 {agent_name} - Suche auf der Seite...")
                    else:
                        progress(f"🔄 {agent_name} - Schritt {step_num}: Verarbeitung läuft...")
                    
                    # Sichere Prüfung für action_output
                    action_output = getattr(step, 'action_output', None)
                    if action_output:
                        output_str = str(action_output)
                        if len(output_str.strip()) > 0:  # Nur nicht-leere Outputs anzeigen
                            output_preview = output_str[:150] + "..." if len(output_str) > 150 else output_str
                            progress(f"✅ {agent_name} - Schritt {step_num} abgeschlossen: {output_preview}")
                    
                    # Sichere Prüfung für Fehler
                    error = getattr(step, 'error', None)
                    if error:
                        error_str = str(error)[:100]
                        progress(f"⚠️ {agent_name} - Schritt {step_num}: Fehler aufgetreten: {error_str}...")
                
                elif isinstance(step, FinalAnswerStep):
                    progress(f"🎯 {agent_name} - Finale Antwort wird erstellt...")
                    
            except Exception as callback_error:
                # Fallback für Callback-Fehler - zeige generische Meldung
                progress(f"🔄 {agent_name} - Schritt wird verarbeitet... (Debug: {str(callback_error)[:50]})")
        
        return step_callback

    progress("Das KI-Modell wird vorbereitet...")
    custom_role_conversions = {"tool-call": "assistant", "tool-response": "user"}
    
    # OpenAI LiteLLM Konfiguration
    litellm_kwargs = dict(
        custom_role_conversions=custom_role_conversions,
        max_completion_tokens=max_completion_tokens,
    )
    
    if api_key:
        litellm_kwargs['api_key'] = api_key
    
    progress(f"🤖 OpenAI LLM wird initialisiert - Modell: {model}")
    
    # reasoning_effort wird nur von o1-Modellen unterstützt
    if model.startswith('o1-'):
        litellm_kwargs['reasoning_effort'] = reasoning_effort
    
    # Debug-Ausgabe für Troubleshooting
    progress(f"🔧 LiteLLM Konfiguration: OpenAI Standard API")
    progress(f"🔧 Verwendetes Modell: {model}")
    
    try:
        model_instance = LiteLLMModel(
            model,
            **litellm_kwargs
        )
        progress("✅ LLM erfolgreich initialisiert")
    except Exception as e:
        error_msg = str(e)
        progress(f"❌ LLM Initialisierung fehlgeschlagen: {error_msg[:100]}")
        progress("💡 Tipp: Prüfe deinen OpenAI API Key und die Internetverbindung")
        raise Exception(f"LLM Initialisierung fehlgeschlagen: {error_msg}")
    # Optionale ProxyManager-Initialisierung (nur wenn explizit aktiviert)
    proxy_kwargs = {}
    
    if use_proxy:
        progress("Proxy-Manager wird initialisiert...")
        try:
            import threading
            
            # Versuche ProxyManager mit Timeout zu initialisieren
            progress("Lade Proxy-Liste (max. 5 Sekunden)...")
            
            result = [None]
            exception = [None]
            
            def target():
                try:
                    result[0] = ProxyManager()
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=5)  # 5 Sekunden Timeout
            
            if thread.is_alive():
                progress("⚠️ Proxy-Manager Timeout - verwende direkte Verbindung")
            elif exception[0]:
                progress(f"⚠️ Proxy-Manager Fehler - verwende direkte Verbindung")
            elif result[0]:
                progress("✅ Proxy-Manager erfolgreich initialisiert")
                proxy_kwargs = result[0].get_request_kwargs()
            else:
                progress("⚠️ Proxy-Manager unbekannter Fehler - verwende direkte Verbindung")
                
        except Exception as e:
            progress(f"⚠️ Proxy-Manager fehlgeschlagen - verwende direkte Verbindung")
    else:
        progress("🚀 Verwende direkte Internetverbindung (schneller)")
    
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    BROWSER_CONFIG = {
        "viewport_size": 1024 * 5,
        "downloads_folder": "downloads_folder",
        "request_kwargs": {
            "headers": {"User-Agent": user_agent},
            "timeout": 300,
            **proxy_kwargs  # Verwende leeres Dict als Fallback
        },
        "serpapi_key": os.getenv("SERPAPI_API_KEY"),
    }
    os.makedirs(f"./{BROWSER_CONFIG['downloads_folder']}", exist_ok=True)
    progress("Browser wird initialisiert...")
    browser = SimpleTextBrowser(**BROWSER_CONFIG)
    browser.ddg_max_results = ddg_max_results
    browser.ddg_region = ddg_region
    browser.ddg_safesearch = ddg_safesearch
    progress("Recherche-Tools werden initialisiert...")
    document_inspection_tool = TextInspectorTool(model_instance, text_limit)
    WEB_TOOLS = [
        SearchInformationTool(browser),
        VisitTool(browser),
        PageUpTool(browser),
        PageDownTool(browser),
        FinderTool(browser),
        FindNextTool(browser),
        ArchiveSearchTool(browser),
        document_inspection_tool,
    ]
    progress("Web-Agent wird vorbereitet...")
    
    # Erstelle Callback für Web-Agent
    web_agent_callback = create_step_callback("Web-Agent")
    
    search_agent = ToolCallingAgent(
        model=model_instance,
        tools=WEB_TOOLS,
        max_steps=max_steps,
        verbosity_level=verbosity,
        step_callbacks=[web_agent_callback],  # Füge Callback hinzu
        planning_interval=planning_interval,
        name="search_agent",
        description="""A team member that will search the internet to answer your question.
    Ask him for all your questions that require browsing the web.
    Provide him as much context as possible, in particular if you need to search on a specific timeframe!
    And don't hesitate to provide him with a complex search task, like finding a difference between two webpages.
    Your request must be a real sentence, not a google search! Like "Find me this information (...)" rather than a few keywords.
    """,
        provide_run_summary=True,
    )
    progress("Manager-Agent wird vorbereitet...")
    
    # Erstelle Callback für Manager-Agent
    manager_agent_callback = create_step_callback("Manager-Agent")
    
    manager_agent = CodeAgent(
        model=model_instance,
        tools=[visualizer, document_inspection_tool],
        max_steps=12,
        verbosity_level=verbosity,
        step_callbacks=[manager_agent_callback],  # Füge Callback hinzu
        additional_authorized_imports=[
            "requests", "zipfile", "os", "pandas", "numpy", "sympy", "json", "bs4", "pubchempy", "xml", "yahoo_finance", "Bio", "sklearn", "scipy", "pydub", "io", "PIL", "chess", "PyPDF2", "pptx", "torch", "datetime", "fractions", "csv"
        ],
        planning_interval=planning_interval,
    )
    progress("🚀 Die Recherche wird gestartet...")
    progress("🤖 Manager-Agent koordiniert die Recherche...")
    
    try:
        # Multi-Runden Recherche
        all_web_results = []
        
        progress(f"🔍 Starte {max_search_rounds} Recherche-Runden...")
        
        for round_num in range(1, max_search_rounds + 1):
            progress(f"🔄 Recherche-Runde {round_num}/{max_search_rounds}")
            
            # Strategische Suchbegriff-Planung durch Manager-Agent
            if round_num == 1:
                # Erste Runde: Grundlegende Recherche
                search_strategy = f"""
Führe eine umfassende Grundrecherche durch zu: {question}

Suche nach:
- Grundlegenden Definitionen und Konzepten
- Aktuellen Entwicklungen und Trends
- Wichtigen Quellen und Experten

Verwende verschiedene Suchbegriffe und besuche mehrere relevante Webseiten.
"""
            else:
                # Weitere Runden: Strategische Vertiefung
                progress(f"🧠 Manager-Agent plant Suchstrategie für Runde {round_num}...")
                
                strategy_prompt = f"""
Basierend auf den bisherigen Recherche-Ergebnissen, plane die nächste Suchstrategie:

**Ursprüngliche Frage:** {question}

**Bisherige Ergebnisse (Runden 1-{round_num-1}):**
{' '.join(all_web_results[-2:]) if len(all_web_results) >= 2 else (all_web_results[0] if all_web_results else 'Keine Ergebnisse')}

**Aufgabe für Runde {round_num}:**
Identifiziere Lücken in der bisherigen Recherche und erstelle eine spezifische Suchstrategie.
Welche Aspekte wurden noch nicht ausreichend abgedeckt?
Welche neuen Suchbegriffe oder Perspektiven sollten erkundet werden?

Erstelle eine präzise Suchanweisung für den Web-Agent.
"""
                
                try:
                    strategy_raw = manager_agent.run(safe_unicode_convert(strategy_prompt))
                    search_strategy = safe_unicode_convert(strategy_raw)
                    progress(f"✅ Suchstrategie für Runde {round_num} geplant")
                except Exception as e:
                    progress(f"⚠️ Fallback-Suchstrategie für Runde {round_num}")
                    search_strategy = f"""
Führe eine ergänzende Recherche durch zu: {question}

Fokus für Runde {round_num}:
- Suche nach spezifischen Details und Beispielen
- Erkunde alternative Perspektiven
- Finde aktuelle Studien oder Statistiken
- Suche nach praktischen Anwendungen
"""
            
            clean_question = safe_unicode_convert(search_strategy)
            
            progress(f"🔍 Runde {round_num}: Search-Agent startet Internetrecherche...")
            
            web_results_raw = search_agent.run(clean_question)
            web_results = safe_unicode_convert(web_results_raw)
            
            # Debug-Information
            results_length = len(str(web_results)) if web_results else 0
            progress(f"✅ Runde {round_num} abgeschlossen. Ergebnislänge: {results_length} Zeichen")
            
            if results_length < 50:
                progress(f"⚠️ Kurze Antwort in Runde {round_num}: '{str(web_results)[:100]}...'")
                # Bei kurzen Antworten, breche ab um Zeit zu sparen
                if round_num >= 3:  # Mindestens 3 Runden wie gewünscht
                    progress(f"⚠️ Recherche nach {round_num} Runden beendet (kurze Antworten)")
                    break
            else:
                all_web_results.append(web_results)
                progress(f"✅ Runde {round_num}: {len(web_results)} Zeichen zu Gesamtergebnis hinzugefügt")
        
        # Kombiniere alle Ergebnisse
        combined_results = "\n\n--- NÄCHSTE RECHERCHE-RUNDE ---\n\n".join(all_web_results)
        progress(f"📊 Alle {len(all_web_results)} Recherche-Runden abgeschlossen. Gesamtlänge: {len(combined_results)} Zeichen")
        
        # Schritt 2: Manager-Agent analysiert die Ergebnisse und erstellt Report
        if combined_results and len(str(combined_results).strip()) > 50:
            progress("📊 Manager-Agent analysiert die kombinierten Suchergebnisse...")
            # Bereinige alle Eingaben für den Manager-Agent
            clean_question_analysis = safe_unicode_convert(question)
            clean_combined_results = safe_unicode_convert(combined_results)
            
            analysis_prompt = f"""
Analysiere die folgenden Rechercheergebnisse aus {len(all_web_results)} Recherche-Runden und erstelle einen umfassenden, strukturierten Report:

**Ursprüngliche Frage:** {clean_question_analysis}

**Kombinierte Rechercheergebnisse aus {len(all_web_results)} Runden:**
{clean_combined_results}

**Aufgabe:**
Erstelle einen detaillierten, gut strukturierten Report mit folgenden Abschnitten:

1. **Executive Summary** - Kurze Zusammenfassung der wichtigsten Erkenntnisse
2. **Detailanalyse** - Ausführliche Untersuchung der verschiedenen Aspekte
3. **Schlüsselfakten** - Wichtige Daten, Zahlen und Fakten
4. **Quellen und Belege** - Auflistung der verwendeten Quellen
5. **Fazit und Empfehlungen** - Schlüsse und praktische Empfehlungen

**Format:** Der Report soll professionell, umfassend und für Laien verständlich sein.
"""
            
            answer_raw = manager_agent.run(analysis_prompt)
            answer = safe_unicode_convert(answer_raw)
            progress("✅ Manager-Agent hat die Analyse und Report-Erstellung abgeschlossen.")
        else:
            progress(f"⚠️ {len(all_web_results)} Recherche-Runden lieferten keine ausreichenden Ergebnisse.")
            # Fallback: Manager-Agent macht eigene Recherche
            progress("🔄 Manager-Agent versucht alternative Recherche...")
            # Bereinige die Eingabe für den Fallback-Prompt
            clean_question_fallback = safe_unicode_convert(question)
            
            fallback_prompt = f"""
Führe eine umfassende Analyse zu folgender Frage durch:

**Frage:** {clean_question_fallback}

**Aufgabe:** Erstelle einen detaillierten Report basierend auf deinem Wissen und verfügbaren Tools.
Der Report soll strukturiert und informativ sein, auch wenn keine aktuellen Internetdaten verfügbar sind.
"""
            answer_raw = manager_agent.run(fallback_prompt)
            answer = safe_unicode_convert(answer_raw)
            progress("✅ Manager-Agent hat die alternative Analyse abgeschlossen.")
            
    except Exception as e:
        progress(f"❌ Fehler bei der Manager-Agent Recherche: {str(e)[:100]}...")
        progress("🔄 Starte direkte Websuche als Fallback...")
        try:
            # Bereinige die Eingabe für den Fallback-Search-Agent
            clean_question_search_fallback = safe_unicode_convert(question)
            answer_raw = search_agent.run(clean_question_search_fallback)
            answer = safe_unicode_convert(answer_raw)
            progress("✅ Fallback-Websuche erfolgreich abgeschlossen.")
        except Exception as fallback_error:
            safe_fallback_error = safe_unicode_convert(str(fallback_error)[:100])
            progress(f"❌ Auch Fallback-Websuche fehlgeschlagen: {safe_fallback_error}...")
            
            # Erstelle eine sichere Fehlermeldung
            safe_original_error = safe_unicode_convert(str(e)[:200])
            safe_fallback_error_full = safe_unicode_convert(str(fallback_error)[:200])
            
            answer = f"""Entschuldigung, bei der Recherche sind Fehler aufgetreten.
            
**Technische Details:**
- Ursprünglicher Fehler: {safe_original_error}
- Fallback-Fehler: {safe_fallback_error_full}

**Mögliche Lösungen:**
1. Versuchen Sie es mit einer anderen Formulierung Ihrer Frage
2. Prüfen Sie Ihre Internetverbindung
3. Versuchen Sie es später erneut

Falls das Problem weiterhin besteht, wenden Sie sich an den Support."""
    
    progress("🎉 Recherche abgeschlossen! Report wird angezeigt.")
    return answer


if submitted:
    if not question or question == 'Stelle eine konkrete Frage, z.B.: "Welche Vor- und Nachteile haben Open Educational Resources für Lehrende?"':
        st.error('⚠️ Bitte gib eine Frage ein!')
    else:
        st.info('🔄 Recherche wird gestartet...')
        progress_bar = st.progress(0)
        status_placeholder = st.empty()
        status_msgs = []
        def status_callback(msg):
            status_msgs.append(msg)
            status_placeholder.info(msg)
            
            # Erweiterte Fortschrittsbalken-Logik für detaillierte Agent-Schritte
            progress_value = 0.0
            
            # Hauptphasen mit Gewichtung
            if "KI-Modell wird vorbereitet" in msg:
                progress_value = 0.05
            elif "Browser wird initialisiert" in msg:
                progress_value = 0.10
            elif "Web-Agent wird vorbereitet" in msg:
                progress_value = 0.15
            elif "Manager-Agent wird vorbereitet" in msg:
                progress_value = 0.20
            elif "🚀 Die Websuche wird gestartet" in msg:
                progress_value = 0.25
            elif "🤖 Web-Agent beginnt" in msg:
                progress_value = 0.30
            
            # Agent-Schritte (Web-Agent Phase: 30-70%)
            elif "Web-Agent - Schritt" in msg and "Planung" in msg:
                progress_value = 0.35
            elif "Web-Agent - Durchsuche das Internet" in msg:
                progress_value = 0.45
            elif "Web-Agent - Besuche Webseite" in msg:
                progress_value = 0.55
            elif "Web-Agent - Analysiere Dokument" in msg:
                progress_value = 0.60
            elif "Web-Agent - Schritt" in msg and "abgeschlossen" in msg:
                progress_value = 0.65
            elif "✅ Web-Agent hat die Recherche abgeschlossen" in msg:
                progress_value = 0.70
            
            # Manager-Agent Phase (70-90%)
            elif "Manager-Agent wird für alternative Analyse gestartet" in msg:
                progress_value = 0.72
            elif "Manager-Agent - Schritt" in msg and "Planung" in msg:
                progress_value = 0.75
            elif "Manager-Agent - Schritt" in msg and "Führe" in msg:
                progress_value = 0.80
            elif "Manager-Agent - Schritt" in msg and "abgeschlossen" in msg:
                progress_value = 0.85
            elif "✅ Manager-Agent hat die alternative Analyse abgeschlossen" in msg:
                progress_value = 0.90
            
            # Finale Phase
            elif "🎯 Websuche war erfolgreich" in msg:
                progress_value = 0.90
            elif "📊 Die Websuche-Ergebnisse werden nun verarbeitet" in msg:
                progress_value = 0.95
            elif "🎉 Recherche abgeschlossen" in msg:
                progress_value = 1.0
            
            # Fehlerbehandlung
            elif "❌ Fehler" in msg:
                current_progress = getattr(status_callback, '_current_progress', 0.0)
                progress_value = max(0.70, current_progress)
            elif "🔄 Starte Fallback-Analyse" in msg:
                progress_value = 0.72
            
            # Aktualisiere Fortschrittsbalken nur wenn sich der Wert erhöht
            current_progress = getattr(status_callback, '_current_progress', 0.0)
            if progress_value > current_progress:
                progress_bar.progress(progress_value)
                status_callback._current_progress = progress_value
        with st.spinner('⏳ Bitte warten, die Anfrage wird bearbeitet...'):
            result = run_research_query(
                model, question, max_steps, verbosity, planning_interval,
                text_limit, reasoning_effort, max_completion_tokens,
                ddg_max_results=max_results,
                ddg_region=region,
                ddg_safesearch=safesearch,
                use_proxy=use_proxy,
                max_search_rounds=max_search_rounds,
                api_key=api_key,
                hf_token=hf_token,
                status_callback=status_callback
            )
        status_placeholder.success("Recherche abgeschlossen!")
        progress_bar.progress(1.0)
        st.markdown("""
        ### 📊 Rechercheergebnis
        ---
        """)
        st.markdown(result)
        st.markdown('### 💾 Ergebnis speichern')
        col1, col2 = st.columns(2)
        txt_data = result
        md_data = f'''# Rechercheergebnis\n\n{result}\n'''
        with col1:
            st.download_button(
                '📄 Als TXT herunterladen',
                data=txt_data,
                file_name='recherche_ergebnis.txt',
                mime='text/plain'
            )
        with col2:
            st.download_button(
                '📝 Als Markdown herunterladen',
                data=md_data,
                file_name='recherche_ergebnis.md',
                mime='text/markdown'
            )
