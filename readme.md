# 🧠 Multi-Agent Corporate Researcher

An interactive chatbot that assists financial investors in conducting comprehensive company background research and financial statement analysis. It leverages powerful LLM agents and web search to deliver detailed corporate insights.

---

## 🚀 Features

- Multi-agent system for deep financial and corporate research
- Real-time web search integration using Brave Search
- Conversational interface for seamless interaction
- Terminal and web UI options

---

## 🔧 Setup Instructions

### 1. Set Required Environment Variables

Ensure the following environment variables are set:

```bash
export OPENAI_API_KEY=your_openai_api_key
export BRAVE_API_KEY=your_brave_search_api_key
````

📝 Use a `.env` file or export them in your shell session.

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🧑‍💻 Usage

### 👉 Launch the Web Chatbot

```bash
chainlit run app.py
```

### 👉 Launch the Terminal Bot

```bash
python terminal_bot.py
```

---

## 📈 Use Case

**Ideal for** financial analysts, investors, and researchers looking to:

* Analyze company profiles
* Perform financial statement analysis
* Gather background info from trusted online sources

---