<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->


<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/Pycomet/escrow-service-bot">
    <img src="images/escrowbot.jpg" alt="Logo" width="200" height="200">
  </a>

  <h2 align="center">Escrow Service Bot (BtcPay)</h2>

  <p align="center">
    An awesome bot to ensure fast and secure trades with a hundred percent transparency
    <br />
    <br />
    <a href="https://t.me/escrowbbot">View Demo</a>
    ·
    <a href="https://github.com/Pycomet/escrow-service-bot/issues">Report Bug</a>
    ·
    <a href="https://github.com/Pycomet/escrow-service-bot/issues">Request New Feature</a>
  </p>
</p>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]
  <a href="https://twitter.com/code_fredy" target="_blank">
    <img alt="Twitter: code_fredy" src="https://img.shields.io/twitter/follow/code_fredy.svg?style=social" />
  </a>

<p>
  <img alt="Version" src="https://img.shields.io/badge/version-version 1-blue.svg?cacheSeconds=2592000" />
  <a href="" target="_blank">
    <img alt="Documentation" src="https://img.shields.io/badge/documentation-yes-brightgreen.svg" />
  </a>
</p>




<!-- TABLE OF CONTENTS -->
## Table of Contents

* [Problem Solved](#problem-solved)
* [About the Project](#about-the-project)
  * [Ideal Users](#ideal-users)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Running the Bot](#running-the-bot)
  * [Local Development (Polling Mode)](#local-development-polling-mode)
  * [Webhook Mode (Production)](#webhook-mode-production)
  * [Local Testing with Webhook](#local-testing-with-webhook)
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [Donation](#donation)
* [License](#license)
* [Author](#contact)

## Local Development

To run the application locally with ngrok, use the `dev.sh` script:

1. **Start Local Development**:
   ```bash
   ./dev.sh start
   ```
   This will start the application with ngrok, set up the webhook, and display the ngrok URL.

2. **Stop Local Development**:
   ```bash
   ./dev.sh stop
   ```
   This will stop the application and ngrok.

3. **Check Status**:
   ```bash
   ./dev.sh status
   ```
   This will show the current status of the local services.

4. **View Logs**:
   ```bash
   ./dev.sh logs
   ```
   This will display the logs for the application and ngrok.

5. **Show URLs**:
   ```bash
   ./dev.sh urls
   ```
   This will display the current ngrok and webhook URLs.

6. **Check Webhook Status**:
   ```bash
   ./dev.sh webhook
   ```
   This will check the current webhook status with Telegram.

## Production Deployment

To deploy the application to production using Docker, use the `deploy.sh` script:

1. **Deploy to Production**:
   ```bash
   ./deploy.sh start
   ```
   This will build and start the Docker containers, set up the webhook, and display the deployment status.

2. **Stop Production Services**:
   ```bash
   ./deploy.sh stop
   ```
   This will stop all running Docker containers.

3. **Restart Production Services**:
   ```bash
   ./deploy.sh restart
   ```
   This will restart all running Docker containers.

4. **Check Deployment Status**:
   ```bash
   ./deploy.sh status
   ```
   This will show the current status of the production deployment.

5. **View Production Logs**:
   ```bash
   ./deploy.sh logs
   ```
   This will display the logs for the production deployment.

6. **Rollback to Previous Version**:
   ```bash
   ./deploy.sh rollback
   ```
   This will rollback the deployment to the previous version.

<!-- PROBLEM SOLVED -->
## Problem Solved

In the world we live in now, business is mostly done on the internet and customers are more unwilling to buy products from sellers they do not trust or have no personal reference to. Knowing they could be mislead or scammed of their money with no trace for refunds.

This is a growing problem and my [escrow Service Bot](https://github.com/Pycomet/escrow-service-bot) is aimed at eradicating the problem, thereby giving large trade group owners and sellers more business. And, also giving buyers the confidence to purchase goods without risk involved.

<!-- ABOUT THE PROJECT -->
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

The Escrow Service Bot offers an automated service acting as an escrow platform, able to facilitate a completely save trade environment on which both the seller and buyer can thrive and do business happily.

All payments are being made through BTCPay Server, providing secure and transparent transactions. The bot supports various payment methods and currencies, ensuring flexibility for both buyers and sellers.

### Ideal Users

* Group Administration (Software As A Service)
* Business Owners
* Freelancers
* Crypto-Traders
* Generally anybody with goods to sell and customers to buy

### Built With

* [PyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI) - Telegram Bot API wrapper
* [Quart](https://pypi.org/project/quart) - Async web framework for webhook support
* [BTCPay Server](https://btcpayserver.org) - Payment processing
* [MongoDB](https://www.mongodb.com) - Database
* [ngrok](https://ngrok.com) - Local webhook testing


<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

* Python 3.8+
* MongoDB
* ngrok (for local webhook testing)
* Telegram Bot Token
* BTCPay Server credentials

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Pycomet/escrow-service-bot.git
cd escrow-service-bot
```

2. Create and activate virtual environment:
```bash
python -m venv env
source env/bin/activate  # Linux/Mac
# or
.\env\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file with required credentials:
```bash
# Bot Configuration
TOKEN=your_telegram_bot_token
SUPPORT_USERNAME=your_support_username
ADMIN_ID=your_admin_id

# BTCPay Configuration
BTCPAY_URL=your_btcpay_url
BTCPAY_API_KEY=your_btcpay_api_key
BTCPAY_STORE_ID=your_btcpay_store_id

# Database Configuration
DATABASE_URL=your_mongodb_url
DATABASE_NAME=your_database_name

# Webhook Configuration
WEBHOOK_MODE=false  # Set to true for production
WEBHOOK_URL=https://your-domain.com/webhook  # Required when WEBHOOK_MODE=true
PORT=5000
```

## Running the Bot

### Local Development (Polling Mode)
1. Set `WEBHOOK_MODE=false` in your `.env` file
2. Run the bot:
```bash
python main.py
```
3. Alternatively, you can also just run
```bash
./dev.sh
```

### Webhook Mode (Production)
1. Set `WEBHOOK_MODE=true` in your `.env` file
2. Configure your webhook URL in `.env`
3. Deploy to your production server

### Local Testing with Webhook
1. Install ngrok:
```bash
# Download ngrok from https://ngrok.com/download
# Configure your authtoken
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

2. Use the deployment script:
```bash
# Make the script executable
chmod +x deploy.sh

# Start the services
./deploy.sh

# Check status
./deploy.sh status

# Stop services
./deploy.sh stop
```

3. Monitor logs:
```bash
# Bot logs
tail -f bot.log

# Ngrok logs
tail -f ngrok.log
```

4. Check ngrok tunnel status:
```bash
curl http://localhost:4040/api/tunnels
```

5. Check bot health:
```bash
curl http://localhost:5000/health
```

6. Check webhook status:
```bash
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
```

## Manual Testing

1. Check if processes are running:
```bash
# Check ngrok
ps aux | grep ngrok

# Check bot
ps aux | grep "python main.py"
```

2. Check ngrok tunnel status:
```bash
curl http://localhost:4040/api/tunnels
```

3. Check bot health:
```bash
curl http://localhost:5000/health
```

4. Check webhook status:
```bash
curl "https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo"
```

<!-- USAGE EXAMPLES -->
## Usage

_Please refer to this article to know more about this project and how the bot is used -> [Documentation](https://medium.com/@alfredemmanuelinyang/how-telegram-escrow-service-bot-is-bound-to-make-a-huge-impact-on-your-business-c533e7cbd0fb?sk=070a3f1b0292c3bea78a85c86b489ac7)_



<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/Pycomet/escrow-service-bot/issues) for a list of proposed features (and known issues). Here is the shortlisted prospects;

- User account rating based on previous trades

- Website to showcase more details information on the bot along with a dashboard to monitor trades (F.A.Q and more)

- Add a button for canceling trades from the buyer's trade memo

- Bot dashboard

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<!-- DONATION -->
## Donation

If you are impressed with my project and wish to buy me a cup of coffee, you can donate to the project through any of the means below

- Bitcoin(BTC) -> 3Lr6duZ7ai4G8KpEqAmeiPSKTcUBt31iZ5
- Etherium(ETH) -> 0x56B7534EED80591033F63DD8D5dCaa3efAC4a92B
- Bitcoin Cash(BCH) -> qqqvhf966xhtv2ak4t9jpey5tq2f4v54dg0ezwdp5t
- Dodgecoin(DOGE) -> DHMy5s96gCx1vwGLQEsYHZeumPbjQzsWUJ


Thanks

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- AUTHOR -->
## Author

* **Alfred Emmanuel Inyang (Codefred) - [![My Website][website]]**



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/Pycomet/escrow-service-bot.svg?style=flat-square
[contributors-url]: https://github.com/Pycomet/escrow-service-bot/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Pycomet/escrow-service-bot.svg?style=flat-square
[forks-url]: https://github.com/Pycomet/escrow-service-bot/network/members
[stars-shield]: https://img.shields.io/github/stars/Pycomet/escrow-service-bot.svg?style=flat-square
[stars-url]: https://github.com/Pycomet/escrow-service-bot/stargazers
[issues-shield]: https://img.shields.io/github/issues/Pycomet/escrow-service-bot.svg?style=flat-square
[issues-url]: https://github.com/Pycomet/escrow-service-bot/issues
[license-shield]: https://img.shields.io/github/license/Pycomet/escrow-service-bot.svg?style=flat-square
[license-url]: https://github.com/Pycomet/escrow-service-bot/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/alfredemmanuelinyang
[product-screenshot]: images/screenshot.png
[website]: https://codefred.me
