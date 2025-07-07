# 🦆 Open Duck Research

**Eine erweiterte Open-Source Implementierung für intelligente Internetrecherche!**

Diese App ermöglicht umfassende, multi-runden Internetrecherchen mit KI-Agenten und bietet sowohl eine Kommandozeilen- als auch eine benutzerfreundliche Web-Oberfläche.

## 📚 Abstammung

Basiert auf dem [Open Deep Research Beispiel](https://github.com/huggingface/smolagents/tree/main/examples/open_deep_research) von HuggingFace smolagents, erweitert um Multi-Runden-Recherche, strategische Suchplanung und robuste Unicode-Behandlung.

## ✨ Hauptfeatures

- **🔄 Multi-Runden Recherche**: Konfigurierbare Anzahl von Recherche-Zyklen (3-10 Runden)
- **🧠 Intelligente Suchstrategie**: Manager-Agent plant strategisch jede Recherche-Runde
- **🌐 Robuste Web-Suche**: DuckDuckGo Integration mit Proxy-Unterstützung
- **📊 Streamlit Web-UI**: Benutzerfreundliche Oberfläche mit Echtzeit-Progress
- **🛡️ Unicode-sicher**: Robuste Behandlung von Sonderzeichen und Encoding-Problemen
- **⚙️ Hochkonfigurierbar**: Detaillierte Einstellungen für alle Parameter 

## Installation

### ⚠️ Wichtige Hinweise

- **🎵 ffmpeg**: Für Audiofunktionen muss ffmpeg installiert und im Systempfad verfügbar sein
  - Download: https://ffmpeg.org/download.html
- **🔍 DuckDuckGo**: Das Paket `duckduckgo_search` wurde durch `ddgs` ersetzt
  - Installation: `pip install ddgs`
- **💬 Chat-Templates**: Eigene Templates in `chat_template.jinja` auslagern
- **🔑 Token-Priorität**: Umgebungsvariablen haben Vorrang vor UI-Eingaben
- **🌐 Proxy-Start**: Proxies sind standardmäßig deaktiviert für schnelleren App-Start
- **📊 Multi-Runden**: Mindestens 3 Runden werden immer ausgeführt, auch bei kurzen Antworten

To install it, first run
```bash
pip install -r requirements.txt
```

And install smolagents dev version
```bash
pip install -e .[dev]
```

## Usage

### Command Line Interface (run.py)

You can use the command line interface by running run.py with various parameters:

```bash
python run.py --model-id "o1" --question "Your question here!"
```

#### Available Parameters

- `--model-id`: Model identifier (default: "o1")
- `--api-base`: Custom API base URL (optional)
- `--question`: Your research question
- `--max-steps`: Maximum number of steps (default: 20)
- `--verbosity`: Verbosity level 0-2 (default: 2)
- `--planning-interval`: Planning interval (default: 4)
- `--text-limit`: Text limit for processing (default: 100000)
- `--reasoning-effort`: Reasoning effort level ["low", "medium", "high"] (default: "high")
- `--max-completion-tokens`: Maximum completion tokens (default: 8192)
- `--ddg-max-results`: Maximum DuckDuckGo search results (default: 10)
- `--ddg-region`: DuckDuckGo region (default: "de-de")
- `--ddg-safesearch`: DuckDuckGo safesearch ["on", "moderate", "off"] (default: "moderate")

### 🌐 Streamlit Web Interface (Empfohlen)

Für eine benutzerfreundliche Web-Oberfläche verwende die Streamlit App:

```bash
streamlit run app.py
```

**Die Web-Oberfläche bietet:**
- 🤔 **Intuitive Frageneingabe** mit Beispielen
- 📊 **Echtzeit-Progress** mit detaillierten Agent-Schritten
- ⚙️ **Umfassende Konfiguration** aller Parameter über die Seitenleiste
- 🔄 **Multi-Runden Kontrolle** (3-10 Recherche-Runden einstellbar)
- 🌐 **Proxy-Management** für anonymere Recherche
- 📝 **Strukturierte Berichte** mit Markdown-Formatierung
- 🧠 **Strategische Recherche-Planung** durch Manager-Agent

## 🚀 Erweiterte Features

### 🔄 Multi-Runden Recherche-System

**Intelligente Recherche-Strategie:**
- **Runde 1**: Grundlegende Recherche (Definitionen, Konzepte, Trends)
- **Runde 2+**: Manager-Agent analysiert bisherige Ergebnisse und plant spezifische Suchstrategien
- **Automatische Lücken-Erkennung**: Identifiziert was noch nicht abgedeckt wurde
- **Strategische Vertiefung**: Neue Suchbegriffe und Perspektiven pro Runde
- **Intelligenter Abbruch**: Bei wiederholten kurzen Antworten nach mindestens 3 Runden

### 🌐 Robuste Proxy-Unterstützung

**Automatische Proxy-Rotation zur Vermeidung von Rate-Limiting:**
- 🇩🇪 **Deutsche Proxies** von spys.one
- 🌍 **Internationale Proxies** von free-proxy-list.net
- ⚡ **5-Sekunden Timeout** verhindert App-Hängen
- ✅ **Proxy-Validierung** vor Verwendung
- 🔄 **Automatische Pool-Aktualisierung** alle 5 Minuten
- 📊 **UI-Kontrolle** über Checkbox (Standard: deaktiviert für schnelleren Start)

### 🔍 Such-Engines

**Unterstützte Suchmaschinen:**
- **DuckDuckGo** (primär) - keine API-Keys erforderlich
- **Google Search** (optional) - mit SERPAPI_API_KEY
- **Konfigurierbare Parameter**: Region, SafeSearch, Ergebnis-Anzahl

## 🔧 Konfiguration

### Umgebungsvariablen

Erstelle eine `.env` Datei mit folgenden Variablen:

```env
# Erforderlich für HuggingFace Modelle
HF_TOKEN=your_huggingface_token_here

# Optional für Google Search
SERPAPI_API_KEY=your_serpapi_key_here

# Optional für OpenAI API
OPENAI_API_KEY=your_openai_key_here
```

### 📊 Parameter-Übersicht

| **Parameter** | **Beschreibung** | **Standard** | **Bereich** |
|---|---|---|---|
| **Recherche-Runden** | Anzahl kompletter Such-Zyklen | 5 | 3-10 |
| **Max. Schritte** | Einzelaktionen pro Agent pro Runde | 20 | 1-100 |
| **Planungsintervall** | Strategie-Überdenken nach X Schritten | 3 | 1-20 |
| **Detailgrad** | Interne Agent-Logs (nicht Report-Qualität) | 1 | 0-2 |
| **Textlimit** | Max. Zeichen pro Quelle | 100.000 | 1.000-500.000 |
| **DuckDuckGo Ergebnisse** | Max. Suchergebnisse pro Runde | 10 | 1-100 |

## 🛠️ Troubleshooting

### Rate-Limiting Probleme
1. ✅ **Automatische Proxy-Rotation** ist aktiviert
2. 📊 **Proxy-Status** wird in der Ausgabe angezeigt
3. 🔄 **Pool-Aktualisierung** alle 5 Minuten
4. ⚙️ **Reduziere `ddg-max-results`** bei anhaltenden Problemen
5. 🌐 **Aktiviere Proxies** über die Checkbox in der Seitenleiste

### Unicode/Encoding Probleme
- ✅ **Automatische UTF-8 Konvertierung** für alle Ein- und Ausgaben
- 🔄 **Ligatur-Ersetzung** (ffi → ffi, etc.)
- 🛡️ **Fallback-Mechanismen** bei Encoding-Fehlern

### Performance-Optimierung
- 🚀 **Weniger Runden + Mehr Schritte** = Schneller aber fokussierter
- 🔍 **Mehr Runden + Weniger Schritte** = Langsamer aber umfassender
- ⚡ **Proxies deaktivieren** für schnelleren Start (Standard)
- 📊 **Detailgrad reduzieren** für weniger Debug-Output
