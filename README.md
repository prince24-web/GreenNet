# GreenNet — Offline Agricultural Assistant for Nigerian Smallholder Farmers

GreenNet is an offline desktop application designed to provide smallholder farmers in Nigeria with reliable, instant agronomic advice, market price statistics, and plant disease diagnostics. Developed for offline hackathon environments (such as Ubuntu 22.04 LTS systems with Intel Core i5 / Ryzen 5 CPUs and 8GB of RAM), it operates entirely without internet access once installed.

---

## 🌟 Key Features

1. **Local Conversational AI**: Powering chat advice using a quantized local model `qwen2.5:1.5b` served via Ollama. It can respond in English, local terminologies, or Pidgin style.
2. **Offline Retrieval-Augmented Generation (RAG)**: Uses local vector storage (`ChromaDB` and `nomic-embed-text` embeddings) containing curated agricultural profiles, pest guides, soil preparation recommendations, and crop management practices.
3. **Structured Agricultural Database**: An offline `SQLite` database pre-populated with detailed profiles of **20 major Nigerian crops** (e.g., Cassava, Maize, Yam, Egusi, Sorghum), active pest treatments (with costs estimated in Nigerian Naira ₦), and local market price listings.
4. **Plant Disease Vision Analysis**: Fast crop disease identification via plant leaf uploads. Uses an optimized **MobileNetV3 ONNX model** (trained on PlantVillage dataset) with a **rule-based color-pattern analyzer fallback** if the model is not downloaded.
5. **High-Performance Desktop GUI**: Runs inside a native desktop webview (`pywebview`), avoiding the massive RAM/disk overhead of Electron or full-browser servers (Gradio/Streamlit), fitting comfortably within an 8GB memory footprint.

---

## 🛠️ System Prerequisites

### 1. Operating System Packages (Critical for Linux/Ubuntu)
On **Ubuntu 22.04 LTS** (or other Debian-based systems), `pywebview` relies on GTK and WebKit. Run the following command in terminal to install the system dependencies:
```bash
sudo apt-get update
sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-webkit2-4.0
```

### 2. Local LLM Service (Ollama)
GreenNet requires Ollama to run the models locally.
* **Linux/Ubuntu Installation**:
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ```
* **Windows Installation**: Download the installer from [Ollama's website](https://ollama.com).

Once Ollama is installed, download the required models while online:
```bash
# Pull the chat model
ollama pull qwen2.5:1.5b

# Pull the embeddings model
ollama pull nomic-embed-text
```

---

## 🚀 Installation & Setup

1. **Clone or Extract the Project Directory**
   Ensure you are in the project folder containing `app.py`.

2. **Set Up a Python Virtual Environment**
   ```bash
   python -m venv venv
   ```
   * Activate the environment:
     * **Linux/Ubuntu/macOS**:
       ```bash
       source venv/bin/activate
       ```
     * **Windows (PowerShell)**:
       ```bash
       .\venv\Scripts\Activate.ps1
       ```
     * **Windows (CMD)**:
       ```bash
       .\venv\Scripts\activate.bat
       ```

3. **Install Python Packages**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Initialize and Seed the Offline Data**
   Run the setup sequence to create your databases and download the vision model:
   ```bash
   # 1. Create and seed the SQLite relational database (crops, treatments, prices)
   python setup_db.py

   # 2. Build the ChromaDB vector database (embeds knowledge sheets using Ollama)
   # Make sure the Ollama service is running (e.g. 'ollama serve' in background)
   python setup_rag.py

   # 3. Download the ONNX Plant Disease Classification model
   python download_model.py
   ```

---

## 💻 Running the Application

Ensure Ollama is running (`ollama serve`), activate your virtual environment, and run:
```bash
python app.py
```
This opens the GreenNet desktop interface.

---

## ⚙️ How It Works (Performance Optimizations)

GreenNet is highly optimized to run smoothly on lower-tier hardware (like Intel Pentium Silver or standard Core i5 laptops):

* **Model Warm-up Thread**: On app startup, a background worker thread pre-loads both `qwen2.5:1.5b` and `nomic-embed-text` into memory with infinite keep-alive (`keep_alive: -1`). This eliminates the 40-60 second "cold start" delay on your first query.
* **Conversational Short-Circuit**: Simple greetings or messages under 40 characters that do not contain agricultural keywords bypass the RAG embedding query entirely. This saves precious CPU cycles and speeds up everyday interactions.
* **Context Optimization**: LLM context window size (`num_ctx`) is restricted to **1024 tokens**, and max generation length is set to **300 tokens**. This provides quick generation times on CPU and keeps memory usage low.
* **Visual Skeleton Transition**: The user interface displays a loading skeleton with friendly, psychological progress updates (e.g., *"Scanning your crop knowledge base..."*) and transitions to the streaming response immediately when the first token is received from the LLM, making the app feel responsive.
