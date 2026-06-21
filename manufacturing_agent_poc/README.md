# TwinSentrix Manufacturing AI Agent POC

This is an internal proof-of-concept dashboard for manufacturing warning explanations. It implements the GUI/Agent layer only: mock IDN prediction parsing, rule-based warning flags, local Markdown retrieval, and an Ollama-backed explanation agent.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

For a fixed local port:

```bash
streamlit run app.py --server.port 8512
```

Optional local LLM setup:

```bash
ollama serve
ollama pull llama3.1:8b
```

If Ollama is not running, the app still works with a deterministic offline explanation so the GUI can be reviewed.

## Data Contract

Each row in `data/mock_idn_predictions.txt` is one machine snapshot:

```text
IDN|ts=<timestamp>|line=<line_id>|machine=<machine_id>|name=<machine_name>|state=<state>|horizon=<minutes>|risk=<0-1>|mode=<failure_mode>|conf=<0-1>|downtime=<minutes>|throughput=<units_per_hr>|baseline=<units_per_hr>|queue=<length>/<capacity>|temp=<celsius>|vib=<rms>|power=<kw>|rul=<minutes>|unc=<0-1>|signals=<signal1,signal2>
```

Future temporal neural network output should either emit this contract or be adapted in `src/idn_parser.py`.

## Knowledge Base

Markdown files in `knowledge_base/` are split by heading and retrieved by machine, failure mode, active flags, and user question. Press **Reload Knowledge Base** in the sidebar after editing docs.

## Project Structure

```text
app.py
data/mock_idn_predictions.txt
knowledge_base/*.md
src/idn_parser.py
src/data_loader.py
src/flag_engine.py
src/severity.py
src/file_retrieval.py
src/agent.py
src/ui_components.py
```

The current mock dataset includes healthy, critical overheating, queue bottleneck, and high-uncertainty snapshots so the sidebar timestamp selector can preview the main dashboard states from the design references.
