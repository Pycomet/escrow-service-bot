# Escrow Service Bot

A secure Telegram bot for facilitating escrow services with cryptocurrency payments through BTCPay Server.

![Escrow Bot](images/escrowbot.jpg)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker (for production)
- ngrok (for local development)
- Telegram Bot Token
- BTCPay Server setup

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Pycomet/escrow-service-bot.git
   cd escrow-service-bot
   ```

2. **Install dependencies**:
   ```bash
   make install-dev
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start development environment**:
   ```bash
   make dev
   ```

## 🛠️ Development Workflow

This project uses a comprehensive Makefile for all development tasks:

### Code Quality
```bash
make format          # Format code with black and isort
make lint            # Run linting with flake8 and mypy
make check           # Run both formatting and linting
```

### Testing
```bash
make test            # Run all tests
make test-unit       # Run unit tests only
make test-coverage   # Run tests with coverage report
```

### Development & Deployment
```bash
make dev             # Start development environment (ngrok + bot)
make deploy          # Deploy to production (Docker)
make status          # Check system status
```

### Quick Development Cycle
```bash
make dev-cycle       # Format, lint, test, and start dev environment
```

**View all available commands**:
```bash
make help
```

## 📋 Features

### Core Functionality
- **Secure Escrow Service**: Automated escrow platform for safe trading
- **Multi-Cryptocurrency Support**: Bitcoin, Ethereum, and other major cryptocurrencies
- **BTCPay Integration**: Secure payment processing through BTCPay Server
- **Telegram Bot Interface**: User-friendly chat-based interface

### Admin Features
- **Wallet Management**: View and manage user wallets
- **Balance Monitoring**: Real-time cryptocurrency balance tracking
- **Trade Oversight**: Monitor all active trades
- **System Statistics**: Platform usage analytics

### Security Features
- **Multi-Signature Wallets**: Enhanced security for funds
- **Encrypted Storage**: Secure handling of sensitive data
- **Audit Trails**: Complete transaction history
- **Admin Controls**: Restricted access to sensitive operations

## 🤖 Bot Commands & Features

### 📱 User Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/start` | Welcome message and main menu | Start interacting with the bot |
| `/help` | Show help information | Get assistance and guidance |
| `/trade` | Create a new trade | Initiate a new escrow transaction |
| `/join` | Join an existing trade | Enter a trade ID to join as buyer |
| `/status` | Show your active trades | View current trade status |
| `/history` | View trade history | See completed and past trades |
| `/wallet` | Manage your wallets | View and manage crypto wallets |
| `/editwallet` | Edit wallet settings | Modify wallet configurations |
| `/rules` | Platform trading rules | Read terms and conditions |
| `/community` | Community guidelines | Community rules and info |
| `/review` | Review completed trades | Rate and review trading partners |
| `/report` | Report issues | Report problems or disputes |
| `/affiliate` | Affiliate program | Join referral program |
| `/broker` | Become a broker | Apply for broker status |
| `/disputes` | Dispute resolution | Handle trade disputes |
| `/cancel` | Cancel current action | Stop ongoing processes |

### 👨‍💼 Admin Commands

| Command | Description | Access Level |
|---------|-------------|--------------|
| `/admin` | Access admin panel | Admin only |
| `/debug` | Debug user state | Admin only |
| `/delete_trade` | Delete trades | Admin only |

### 🔄 Interactive Features

#### Trade Management
- **Create Trades**: Step-by-step trade creation with multiple cryptocurrencies
- **Join Trades**: Simple trade joining with ID verification
- **Payment Proof**: Upload images/documents as payment evidence
- **Status Tracking**: Real-time trade status updates
- **Dispute Resolution**: Built-in mediation system

#### Wallet Operations
- **Multi-Wallet Support**: Create and manage multiple crypto wallets
- **Balance Checking**: Real-time balance updates
- **Transaction History**: Complete transaction logs
- **Wallet Refresh**: Manual balance refresh options

#### Broker System
- **Broker Registration**: Apply to become a verified broker
- **Commission Tracking**: Automatic commission calculations
- **Reputation System**: Rating and review system for brokers
- **Trade Mediation**: Professional dispute resolution

### 🎯 State-Based Interactions

The bot uses intelligent state management to handle complex workflows:

- **Trade Creation Flow**: Multi-step process with validation
- **Join Process**: Trade ID verification and buyer onboarding  
- **Broker Registration**: Multi-step application process
- **Report System**: Structured issue reporting
- **Admin Operations**: Secure administrative functions

### 📊 Handler Architecture

The bot uses a priority-based handler system to ensure proper message routing:

| Priority | Handler Type | Purpose |
|----------|--------------|---------|
| **Group 0** | Command Handlers | Process all bot commands |
| **Group 1** | Join Flow | Handle trade joining process |
| **Group 2** | Broker Flow | Handle broker registration |
| **Group 3** | Report Flow | Handle issue reporting |
| **Group 5** | Trade Flow | Handle trade creation |
| **Group 10** | Admin Flow | Handle admin operations |

This architecture prevents handler conflicts and ensures reliable message processing.

## 🏗️ Architecture

```
escrow-service-bot/
├── handlers/          # Telegram bot command handlers
├── functions/         # Core business logic
├── payments/          # Payment processing (BTCPay, etc.)
├── database/          # Database models and types
├── utils/             # Utility functions and helpers
├── tests/             # Test suite
├── main.py           # Application entry point
├── config.py         # Configuration management
└── Makefile          # Development workflow automation
```

## 🧪 Testing

The project includes comprehensive tests:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **Service Tests**: End-to-end service testing

Run tests with coverage:
```bash
make test-coverage
```

## 🚀 Deployment

### Development Environment
```bash
make dev              # Start with ngrok for webhook testing
make dev-stop         # Stop development environment
make dev-logs         # Monitor development logs
```

### Production Deployment
```bash
make deploy           # Deploy using Docker
make deploy-stop      # Stop production deployment
make deploy-logs      # Monitor production logs
```

## 📁 Project Structure

```
├── handlers/                 # Telegram bot handlers
│   ├── admin.py             # Admin commands
│   ├── trade_flows/         # Trade process handlers
│   └── webhook.py           # Webhook processing
├── functions/               # Core business logic
│   ├── broker.py            # Broker functionality
│   ├── trade.py             # Trade management
│   ├── user.py              # User management
│   └── wallet.py            # Wallet operations
├── payments/                # Payment processors
│   └── btcpay.py            # BTCPay integration
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── service/             # Service tests
├── utils/                   # Utilities
│   ├── enums.py             # Enumerations
│   ├── keyboard.py          # Telegram keyboards
│   └── messages.py          # Message templates
├── main.py                  # Application entry point
├── config.py                # Configuration
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Docker configuration
├── Makefile                 # Development automation
└── README.md               # This file
```

## 🔧 Configuration

Create a `.env` file with the following variables:

```env
# Telegram Bot Configuration
TOKEN=your_telegram_bot_token
ADMIN_ID=your_admin_telegram_id

# Database Configuration
DATABASE_URL=mongodb://localhost:27017
DATABASE_NAME=escrowbot

# BTCPay Configuration
BTCPAY_URL=https://your-btcpay-server.com
BTCPAY_STORE_ID=your_store_id
BTCPAY_API_KEY=your_api_key

# Webhook Configuration (for production)
WEBHOOK_MODE=true
WEBHOOK_URL=https://your-domain.com/webhook
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and run tests: `make test-cycle`
4. Commit your changes: `git commit -m 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the code comments and docstrings
- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/Pycomet/escrow-service-bot/issues)
- **Telegram**: Contact the bot directly at [@escrowbbot](https://t.me/escrowbbot)

## 🙏 Acknowledgments

- BTCPay Server for secure payment processing
- Python Telegram Bot library for Telegram integration
- MongoDB for data storage
- All contributors and users of this project

---

**Built with ❤️ for secure trading**
