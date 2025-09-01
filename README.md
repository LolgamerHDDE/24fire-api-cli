# 24fire-api-cli

A command-line interface (CLI) tool for managing your [24Fire.de](https://24fire.de) services via their API.  
This tool helps you control KVM servers, manage backups, view traffic statistics, monitor outages/readings, configure DDoS protection, and edit DNS records — all from your terminal.

---

## ✨ Features

- 🔧 **KVM Server Management**
  - Start, stop, restart servers
  - View detailed server information (credentials, IPs, specs, OS, monitoring)

- 💾 **Backups**
  - List, create, restore, and delete backups
  - Colorized and structured output with summaries

- 📊 **Traffic**
  - View current usage and monthly logs
  - Usage breakdown with progress bars and statistics

- 📡 **Monitoring**
  - Outage statistics and incident history
  - Performance readings (CPU, memory, ping) with summaries and alerts

- 🛡 **DDoS Protection**
  - View Layer 4/7 protection status
  - Protection scoring and security recommendations

- 🌐 **Domains & DNS**
  - Add, edit, and remove DNS records

- ⚙️ **Automations**
  - Install automation scripts remotely via SSH/SFTP
  - Execute custom commands on your servers

---

## 📦 Installation

Clone this repository and install dependencies:

```bash
git clone https://github.com/LolgamerHDDE/24fire-api-cli.git
cd 24fire-api-cli
pip install -r requirements.txt
````

> ⚠ Requires Python 3.8+

---

## 🔑 Configuration

The CLI uses your **24Fire API key**, which can be stored in a `.env` file:

```
X_FIRE_APIKEY=your_api_key_here
```

Alternatively, you can pass it via command-line arguments.

---

## 🚀 Usage

Run the CLI with:

```bash
python main.py [command] [options]
```

### Examples

* **Start a KVM server**:

  ```bash
  python main.py kvm control my-server-name start
  ```

* **List backups**:

  ```bash
  python main.py backup list my-server-id
  ```

* **Show traffic usage**:

  ```bash
  python main.py traffic usage my-server-id
  ```

* **Check monitoring outages**:

  ```bash
  python main.py monitoring outages my-server-id
  ```

* **View DDoS protection**:

  ```bash
  python main.py ddos my-server-id
  ```

* **Add a DNS record**:

  ```bash
  python main.py dns add my-domain.com A www 1.2.3.4
  ```

---

## 📋 Requirements

* Python 3.8+
* Dependencies:

  * `requests`
  * `paramiko`
  * `python-dotenv`

Install via:

```bash
pip install -r requirements.txt
```

---

## ⚠️ Disclaimer

This is an **unofficial CLI tool** for 24Fire.de.
Use at your own risk — actions like stopping servers or deleting backups are irreversible.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.