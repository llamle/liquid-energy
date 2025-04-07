# Liquid Energy

An algorithmic market making bot for energy assets using the Hummingbot framework with Machine Learning and Reinforcement Learning capabilities.

[![Continuous Integration](https://github.com/llamle/liquid-energy/actions/workflows/ci.yml/badge.svg)](https://github.com/llamle/liquid-energy/actions/workflows/ci.yml)
[![Continuous Deployment](https://github.com/llamle/liquid-energy/actions/workflows/cd.yml/badge.svg)](https://github.com/llamle/liquid-energy/actions/workflows/cd.yml)

## Project Overview

Liquid Energy is designed to provide efficient market making services for energy asset markets, using advanced ML and RL techniques to optimize trading strategies. The system integrates with the Hummingbot framework and implements sophisticated algorithms for price prediction, anomaly detection, and dynamic strategy adjustment.

## Development Approach

This project strictly follows Test-Driven Development (TDD) principles:

1. Write comprehensive tests that define expected behavior before implementation
2. Demonstrate tests failing (red phase)
3. Implement the minimum code needed to pass tests (green phase)
4. Refactor while maintaining passing tests (refactor phase)
5. Verify all tests pass before proceeding to the next component

## Project Structure

```
liquid-energy/
├── docs/
│   ├── components/      # Component documentation
│   ├── development/     # Development processes and guidelines
│   ├── refactoring/     # Refactoring recommendations
│   └── requirements/    # Detailed requirements
├── src/
│   └── liquid_energy/
│       ├── core/        # Core components 
│       ├── ml/          # Machine learning components
│       ├── rl/          # Reinforcement learning components
│       └── strategies/  # Trading strategies
└── tests/
    ├── unit/            # Unit tests
    └── integration/     # Integration tests
```

## Development Progress

### Phase 1: Foundational Architecture

| Component | Requirements | Tests | Implementation | Refactoring | Documentation | Status |
|-----------|:------------:|:-----:|:--------------:|:-----------:|:-------------:|:------:|
| Core Event System | ✅ | ✅ | ✅ | ✅ | ✅ | Complete |
| Hummingbot API Integration | ✅ | ✅ | ✅ | ✅ | ✅ | Complete |
| Energy Market Data Connectivity | 🔜 | 🔜 | 🔜 | 🔜 | 🔜 | Pending |
| Base Market Making Strategy | 🔜 | 🔜 | 🔜 | 🔜 | 🔜 | Pending |
| Configuration System | 🔜 | 🔜 | 🔜 | 🔜 | 🔜 | Pending |
| Logging and Monitoring | 🔜 | 🔜 | 🔜 | 🔜 | 🔜 | Pending |

### Phases 2-6

Pending completion of Phase 1.

## Getting Started

### Prerequisites

- Python 3.8+
- Hummingbot framework
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/llamle/liquid-energy.git
   cd liquid-energy
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Run the tests:
   ```bash
   pytest
   ```

## Core Components

### Event-Driven Architecture

The event-driven architecture is the foundation of the Liquid Energy trading system. It enables decoupled components to communicate through events, providing a flexible and extensible framework for market data processing, strategy execution, and trade management.

Learn more in [Event System Documentation](docs/components/event_system.md).

### Hummingbot API Integration

The Hummingbot client provides a robust interface for executing trades and accessing market data through the Hummingbot trading engine. By integrating with the event-driven architecture, it enables building sophisticated trading strategies that can respond to real-time market conditions.

Learn more in [Hummingbot Client Documentation](docs/components/hummingbot_client.md).

## CI/CD Pipeline

Liquid Energy employs a comprehensive CI/CD pipeline to ensure code quality and reliability:

- **Continuous Integration**: Automated testing and code quality checks on all pull requests and commits
- **Continuous Deployment**: Automated release and publishing process when version tags are pushed
- **Dependency Updates**: Weekly automated dependency updates to maintain security and compatibility

For more details, see [CI/CD Process Documentation](docs/development/ci_cd_process.md).

## Contributing

To contribute to this project:

1. Make sure all changes follow the TDD approach
2. Write tests before implementation
3. Ensure all tests pass
4. Follow the refactoring recommendations
5. Document your components

## License

[MIT License](LICENSE)
