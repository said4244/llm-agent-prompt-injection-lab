# LLM Agent Prompt Injection Lab

I built this school lab to explore how prompt injection can steer a tool-using
LLM agent into application vulnerabilities. A fictional banking assistant makes
the relationship between the user prompt, agent tools, SQL queries, and file
exports visible in a Streamlit interface.

The repository contains both versions so I can compare the vulnerable behavior
with selected mitigations side by side.

**Built with:** Python, Streamlit, LangChain, OpenAI, SQLite, Docker.

## The two versions

| Version | Folder | Port | Focus |
| --- | --- | --- | --- |
| Vulnerable | `insecure/` | 8501 | Prompt injection, SQL injection, and unsafe shell exports |
| Mitigation experiment | `secure/` | 8502 | Input filtering, parameterized transaction queries, and Python file exports |

Both versions expose tools for retrieving the current user, reading transactions,
and exporting results. The database helper creates fictional users and
transactions on first use. The mitigations illustrate changes to individual
layers rather than a guarantee that the agent is comprehensively protected.

Run the vulnerable version locally with demo data in an isolated environment.

## Run locally

Use Python 3.10 or newer. From the repository root:

```bash
cd insecure
python -m venv .venv
```

Activate the environment with `.venv\Scripts\Activate.ps1` in PowerShell or
`source .venv/bin/activate` on macOS/Linux. Copy `.env.example` to `.env`, set
your own `OPENAI_API_KEY`, then run:

```bash
python -m pip install -r requirements.txt
streamlit run main.py --server.port 8501
```

For the mitigation experiment, follow the same steps in `secure/` and use port
8502. Keep provider keys in the ignored `.env` files.

## Docker

```bash
cd insecure
docker build -t llm-lab-insecure .
docker run --rm --env-file .env -p 127.0.0.1:8501:8501 llm-lab-insecure
```

For the other version, build from `secure/` and map local port 8502 to container
port 8502. The Docker ignore files exclude credentials and generated lab data
from the image build context.

## Project layout

| Path | Purpose |
| --- | --- |
| `insecure/main.py` | Vulnerable Streamlit application |
| `secure/main.py` | Application with input filtering |
| `insecure/tools.py`, `secure/tools.py` | Tool implementations for comparison |
| `insecure/transaction_db.py`, `secure/transaction_db.py` | Database helpers and synthetic fixtures |
| `docs/exploitation.md` | Lab walkthrough and test payloads |

## Background and attribution

I developed this as part of a Fontys HBO-ICT AI & Cybersecurity group project
(Group L), inspired by [WithSecure Labs’ LLM agent prompt-injection
research](https://labs.withsecure.com/publications/llm-agent-prompt-injection).
The project is licensed under [Apache-2.0](LICENSE).
