# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build, Test, and Development Commands

This project uses a comprehensive Makefile for all development tasks:

### Setup and Installation
```bash
make install          # Install production dependencies
make install-dev      # Install development dependencies (includes linting tools)
```

### Code Quality
```bash
make format           # Format code with black and isort
make lint             # Run linting with flake8 and mypy
make check            # Run both format and lint
```

### Testing
```bash
make test             # Run all tests
make test-unit        # Run unit tests only
make test-integration # Run integration tests only
make test-service     # Run service tests only
make test-coverage    # Run tests with coverage report
```

### Development Environment
```bash
make dev              # Start development environment (ngrok + bot in polling mode)
make dev-stop         # Stop development environment
make dev-status       # Show development environment status
make dev-logs         # Monitor development logs
```

### Production Deployment
```bash
make deploy           # Deploy using Docker and docker-compose
make deploy-stop      # Stop production deployment
make deploy-status    # Show production status
make deploy-logs      # Monitor production logs
```

### Quick Workflows
```bash
make dev-cycle        # Format, lint, test, and start dev environment
make test-cycle       # Format, lint, and test
make ci               # Full CI pipeline: install-dev, format, lint, test-coverage
```

## Architecture Overview

This is a **Telegram escrow service bot** built with Python that facilitates secure cryptocurrency trading between users.

### Core Components Architecture

**Entry Point**: `main.py` - Quart web application with webhook support and bot initialization
- Handles both polling (development) and webhook (production) modes
- Includes health check endpoints and payment webhook processing
- Uses ApplicationProxy pattern to handle testing environments gracefully

**Configuration**: `config.py` - Centralized configuration management
- Environment variable management with sensible defaults
- MongoDB connection setup
- Telegram application initialization with timezone patching for APScheduler compatibility
- Database index creation for optimal query performance

### Directory Structure

```
handlers/           # Telegram bot command and callback handlers (grouped by priority)
├── start.py        # Welcome and main menu
├── initiate_trade.py # Trade creation flow
├── join.py         # Trade joining process
├── broker.py       # Broker registration and management
├── admin.py        # Administrative commands and debug tools
├── callbacks.py    # Inline keyboard callback handling
└── webhook.py      # Payment webhook processing

functions/          # Core business logic modules
├── trade.py        # Trade lifecycle management
├── user.py         # User account and profile management
├── wallet.py       # Cryptocurrency wallet operations
├── broker.py       # Broker system functionality
└── utils.py        # Shared utility functions

utils/              # UI and helper utilities
├── enums.py        # Status enumerations and constants
├── keyboard.py     # Telegram inline keyboard generators
├── messages.py     # Message templates and formatting
└── trade_status.py # Trade state management utilities

payments/           # Payment processing integrations
└── btcpay.py       # BTCPay Server integration for crypto payments

database/           # Database schema and types
├── types.py        # MongoDB document schemas and data models
└── __init__.py     # Database connection exports

tests/              # Comprehensive test suite
├── unit/           # Unit tests for individual components
├── integration/    # Integration tests for component interactions
├── service/        # End-to-end service testing
└── conftest.py     # Pytest configuration and fixtures
```

### Handler Priority System

The bot uses a priority-based handler system to prevent conflicts:
- **Group 0**: Command handlers (highest priority)
- **Group 1**: Join trade flow handlers
- **Group 2**: Broker registration flow handlers
- **Group 3**: Report/dispute flow handlers
- **Group 5**: Trade creation flow handlers
- **Group 10**: Admin operation handlers

### State Management

Uses MongoDB collections for persistent state:
- **users**: User profiles, settings, and broker status
- **trades**: Active and completed trade records with status tracking
- **wallets**: User cryptocurrency wallet information
- **wallet_transactions**: Transaction history and balance tracking

### Key Features

1. **Multi-cryptocurrency Support**: Bitcoin, Ethereum, and other cryptocurrencies via BTCPay Server
2. **Escrow System**: Secure fund holding during trades with automated release
3. **Broker Network**: Verified broker system for dispute resolution and trade mediation
4. **Admin Panel**: Comprehensive administrative tools for trade management and user support
5. **Affiliate System**: Referral program with commission tracking
6. **Review System**: Post-trade rating and review functionality

### Environment Configuration

Required `.env` variables:
- `TOKEN`: Telegram bot token
- `ADMIN_ID`: Telegram user ID for admin access
- `DATABASE_URL`: MongoDB connection string
- `BTCPAY_URL`, `BTCPAY_API_KEY`, `BTCPAY_STORE_ID`: Payment processing
- `WEBHOOK_MODE`: Enable webhook mode for production
- `WEBHOOK_URL`: Public URL for webhook endpoint

### Development Notes

- **Testing Environment**: Uses ApplicationProxy pattern to provide mock implementations during testing
- **Timezone Handling**: Includes APScheduler timezone patches to prevent UTC-related errors
- **Database Indexes**: Automatically creates MongoDB indexes on startup for performance
- **Error Recovery**: Graceful fallback mechanisms for bot initialization failures
- **Community Features**: Scheduled content system with admin management panel
- **Security**: Bot fee calculation, secure wallet management, and admin-only operations

### Code Quality Standards

The project enforces strict code quality with:
- **Black** formatter (88 character line length)
- **isort** import sorting with project-specific configuration
- **flake8** linting with extended ignore rules
- **mypy** type checking (configured for gradual typing)
- **pytest** with comprehensive test coverage and multiple test types

## GitHub Issue Workflow

When a GitHub issue is reported for this repository, follow this automated workflow:

### Issue Analysis and Implementation Process

1. **First, analyze the issue** using the `issue-analyzer` agent:
   - Use the `issue-analyzer` agent to thoroughly analyze the GitHub issue
   - Get detailed implementation instructions and technical analysis
   - Understand the scope, requirements, and potential impact

2. **Then implement the solution** using the `escrow-bot-developer` agent:
   - Use the analysis report from step 1 to guide implementation
   - The `escrow-bot-developer` agent will:
     - Create a new feature branch (not main)
     - Implement the required changes following the codebase patterns
     - Run tests and ensure code quality standards are met
     - Create a pull request against the main branch

### Example Workflow
```
User: "Can you analyze issue #45 and implement the fix?"

1. Use issue-analyzer agent on issue #45
2. Review the analysis report
3. Use escrow-bot-developer agent with the analysis to implement changes
4. Verify the PR is created against main branch
```

This ensures all GitHub issues receive proper analysis before implementation and maintains code quality through the PR review process.Can