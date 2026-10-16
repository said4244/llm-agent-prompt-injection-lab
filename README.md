# LLM Agent Prompt Injection Lab

A small, self-contained lab that shows how a **ReAct-style LLM agent with tool
access** can be driven — through **prompt injection** — into classic
application-security bugs: **SQL injection** and **OS command injection**. It
ships in two builds so you can see the attack *and* the fix side by side:

| Build | Folder | Port | State |
|-------|--------|------|-------|
| 🔴 Vulnerable | [`insecure/`](insecure/) | 8501 | Intentionally exploitable |
| 🟢 Hardened | [`secure/`](secure/) | 8502 | Same app, four defences applied |

The app is a fictional **banking chatbot** ("Group L ChatBot"). It uses
[LangChain](https://python.langchain.com/) + an OpenAI model as the agent, three
tools over a small SQLite database, and [Streamlit](https://streamlit.io/) as the
front end.

> ### ⚠️ Authorization & educational notice
> This project is built for **security education and defensive research**. The
> `insecure/` build is *deliberately* vulnerable. Run it **only locally**, never
> expose it to an untrusted network, and never point it at real data or real
> credentials. Only ever attack systems you own or are explicitly authorized to
> test. The goal here is to understand the failure modes well enough to *prevent*
> them — hence the hardened build and the blue-team notes.

This lab was built for a Fontys HBO-ICT (AI & Cybersecurity) group project and is
inspired by WithSecure Labs' research on
[LLM agent prompt injection](https://labs.withsecure.com/publications/llm-agent-prompt-injection).
A full step-by-step writeup lives on my blog (NL + EN).

---

## The idea in one picture

```
 user prompt ──▶ [ LLM agent (ReAct) ] ──▶ tools ──▶ SQLite DB
                        ▲                      │
                        │                      ▼
             prompt injection          SQL / command injection
         (controls the agent's      (the tools trust whatever the
          Thought/Action/Obs)         agent passes them)
```

An attacker can't call the tools directly — but they *can* talk to the agent. By
injecting fake **Thought / Action / Observation** steps into the chat, they make
the agent believe it already looked up the "current user" and got back an
attacker-chosen `userId`. The tools then faithfully run that value against the
database (and, for the export tool, against the shell).

## The three weaknesses (vulnerable build)

1. **Prompt injection — over-trusting system prompt.**
   `insecure/main.py` tells the model to treat the user as an admin, to pass down
   *any* `userId` the user provides, and to never filter output. That hands
   control of the agent's reasoning to the attacker.
2. **SQL injection — string-formatted query.**
   `insecure/transaction_db.py` builds `SELECT * FROM Transactions WHERE userId =
   '<value>'` by string interpolation. A `UNION SELECT` payload turns a
   single-user lookup into a full `username` + `password` dump.
3. **OS command injection — `os.system()` on user input.**
   `insecure/tools.py` builds `echo '...' > exports/transaction-<user_id>` and
   runs it through the shell, so a crafted `user_id` executes commands as the
   service account.

## The four fixes (hardened build)

| # | Fix | Where |
|---|-----|-------|
| 1 | Least-privilege system prompt: only operate on the id from `GetCurrentUser`, refuse any user-supplied id | `secure/main.py` |
| 2 | Input sanitisation that strips ReAct / SQL / shell patterns (defence in depth, shown in the UI) | `secure/main.py` |
| 3 | Parameterised SQL query + integer validation | `secure/transaction_db.py` |
| 4 | Safe export: `int()` validation, path confinement, plain file write (no shell) | `secure/tools.py` |

See [`docs/exploitation.md`](docs/exploitation.md) for the full attack walkthrough
and the exact payloads.

---

## Running it

**Requirements:** Python 3.9+ and an OpenAI API key (the agent needs an LLM).

### Local (either build)

```bash
cd insecure          # or: cd secure
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                           # then put your OPENAI_API_KEY in .env
streamlit run main.py --server.port 8501       # secure build: use 8502
```

Open the printed URL. The SQLite database (`transactions.db`) is seeded
automatically on first run; it is git-ignored on purpose.

### Docker

```bash
cd insecure
docker build -t llm-lab-insecure .
docker run --rm -p 8501:8501 --env-file .env llm-lab-insecure
```

---

## Repository layout

```
.
├── insecure/            # vulnerable build (port 8501)
├── secure/              # hardened build  (port 8502)
├── docs/
│   ├── exploitation.md  # step-by-step attack + payloads
│   └── screenshots/     # demo images
├── LICENSE              # Apache-2.0
└── README.md
```

## Credits

- Concept & "Damn Vulnerable LLM Agent" inspiration:
  [WithSecure Labs — LLM Agent Prompt Injection](https://labs.withsecure.com/publications/llm-agent-prompt-injection).
- Built by **Said Alhazina** as part of a Fontys HBO-ICT AI & Cybersecurity group
  project (Group L).

## License

Apache-2.0 — see [`LICENSE`](LICENSE).
