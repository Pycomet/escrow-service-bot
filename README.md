
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
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [Donation](#donation)
* [License](#license)
* [Author](#contact)

<!-- PROBLEM SOLVED -->
## Problem Solved

In the world we live in now, business is mostly done on the internet and customers are more unwilling to buy products from sellers they do not trust or have no personal reference to. Knowing they could be mislead or scammed of their money with no trace for refunds.

This is a growing problem and my [escrow Service Bot](https://github.com/Pycomet/escrow-service-bot) is aimed at eradicating the problem, thereby giving large trade group owners and sellers more business. And, also giving buyers the confidence to purchase goods without risk involved.

<!-- ABOUT THE PROJECT -->
## About The Project

<!-- [![Product Name Screen Shot][product-screenshot]](https://example.com) -->

The Escrow Service Bot offers an automated service acting as an escrow platform, able to facilitate a completely save trade environment on which both the seller and buyer can thrive and do business happily.

All payments are being made directly to the respective parties, either through Bitcoin, Ethereum, Litecoin, Ripplecoin or Bitcoin Cash cryptocurrency which ofcourse is predefined by the seller's choice of local currency from the following:

- US Dollars (USD)
- Euros (EUR)
- British Pound (GBP)
- Canadian Dollar (CAD)
- Japanese Yen (JPY)
- The Swiss Franc (CHF)

With an affiliate program being part of the structure, administrators of different Telegram Group platforms are also able to use the [escrow Service Bot](https://github.com/Pycomet/escrow-service-bot) in conducting save and fast business transactions within their groups smoothly, with each transaction being completed secured and easily traceable. Also, each registered group admin is entitled to a charge on every trade carried out by the group members.


### Ideal Users

* Group Administration (Software As A Service)
* Business Owners
* Freelancers
* Crypto-Traders
* Generally anybody with goods to sell and customers to buy

### Built With

This section should list any frameworks/APIs used to build this project application.

* [PyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI) to build the UI/UX feature for user interaction
* [Flask](https://pypi.org/project/Flask) serving the bot as a simple webhook application
* [Heroku](https://heroku.com) server for deployment
* [Coinbase API](https://developers.coinbase.com) to serve as payment gateway


<!-- GETTING STARTED -->
## Getting Started

This section covers how you can get the escrow Service Bot up and running locally with your own credentials in no time. All you need are the following.

### Prerequisites

Here is the list of needed dependencies to have available on your machine(PC)

* python > 3.6 - Goto [link](https://python.org) to download it
* pip
```sh
pip install --upgrade pip
```

### Installation

1. Open the project's [github page](https://github.com/Pycomet/escrow-service-bot) and star this project by tapping on the star button at the top right of the page.

2. Get a bot token key from [@BotFather](https://t.me/BotFather)

3. Create a [Coinbase account](https://coinbase.com) and retrieve your API information. This would be used to set up payment systems for your service bot instance.

4. Clone this repository
```sh
git clone https://github.com/Pycomet/escrow-service-bot.git
```

5. Open the project directory
```sh
cd escrow-service-bot
```

6. Create a virtual environment to install all the app dependencies
```sh
python -m venv env

// Enter into the virtual environment (Linux)
source env/bin/activate
```

7. Install the dependencies
```sh
pip install -r requirements.txt
```

8. Create a `.env` file to house all your credentials
```sh
// Bot token from @Botfather
TOKEN=""

// Coinbase API credentials
API_KEY=""
API_SECRET=""

// Your telegram user id
ADMIN_ID=""

// Database url (here would be based on your personal choice for your database)
DATABASE_URL=""
```

9. Managing database changes with Alembic commands;
```sh
- Generated migration: alembic revision --autogenerate -m "initial"
- Applied migrations: alembic upgrade head
```

10. You are ready to start the application
```sh
python main.py
```

ENJOY!

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
