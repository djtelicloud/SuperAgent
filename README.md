# SuperAgent 🤖

SuperAgent is an autonomous, self-thinking AI agent framework built with Python and [pydantic-ai](https://github.com/pydantic/pydantic-ai). Designed specifically for Azure environments, it can plan complex tasks, execute terminal commands, and reason through results to achieve user-defined goals.

## 🚀 Key Features

- **Self-Thinking & Planning**: Uses a structured internal monologue to decompose tasks into actionable steps.
- **Autonomous Execution**: Capable of running terminal commands (Windows/Linux) and analyzing their output to inform next steps.
- **Azure Optimized**: Built-in support for Azure OpenAI, Azure ML SDK, and `azd`/`az` commands.
- **Rich Terminal UI**: Beautiful CLI interface using the `rich` library for clear visualization of thoughts, plans, and results.
- **Persistent Memory**: Integration with a FastAPI backend for storing, retrieving, and summarizing chat history.
- **Extensible Tools**: Easily add new tools to the agent's capabilities using Pydantic AI's tool system.

## 🛠️ Tech Stack

- **Python 3.10+**
- **LLM Framework**: [pydantic-ai](https://pydantic-ai.com/)
- **AI Model**: Azure OpenAI (GPT-4o recommended)
- **Terminal UI**: [rich](https://github.com/Textualize/rich)
- **API Backend**: FastAPI, Uvicorn
- **Data Tools**: Pandas, NumPy, Scikit-learn
- **Azure Tools**: Azure Identity, Azure Search Documents, Azure Storage Blob

## 📋 Prerequisites

Before you begin, ensure you have:
- Python 3.10 or higher installed.
- An Azure OpenAI instance with a model deployment (e.g., `gpt-4o`).
- Azure credentials for search and storage if using those features.

## ⚙️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/djtelicloud/SuperAgent.git
   cd SuperAgent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory and add your Azure OpenAI credentials:
   ```env
   OPENAI_API_KEY=your_api_key_here
   OPENAI_API_VERSION=2024-02-15-preview
   OPENAI_API_BASE=https://your-resource.openai.azure.com/
   OPENAI_API_DEPLOYMENT=gpt-4o
   ```

## 🎮 Usage

### CLI Mode
Run the agent in interactive CLI mode to start giving it tasks:
```bash
python super_agent.py
```

### Agent Workflow
SuperAgent follows a rigorous 8-step execution loop:
1. **Think & Plan**: Internal reasoning about the task.
2. **Message User**: Explains the intended approach.
3. **Explain Action Plan**: Displays structured steps.
4. **Run Command**: Executes shell/powershell commands if needed.
5. **Re-evaluate**: Reflects on the output of the commands.
6. **Repeat**: Continues until the goal status is `Completed`.

## 📂 Project Structure

- `super_agent.py`: The main entry point and core logic of the agent.
- `azure_agent.py`: Configuration and initialization of the Azure OpenAI model.
- `agent_prompts.py`: Defines the system prompts and core reasoning principles.
- `chat_history.py`: Utilities for managing session context.
- `messages_util.py`: Helper functions for message processing.
- `requirements.txt`: Project dependencies.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

[Add License Type Here - e.g., MIT]
