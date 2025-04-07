# CI/CD Process

Liquid Energy follows automated Continuous Integration and Continuous Deployment practices to ensure code quality, maintainability, and reliability.

## CI/CD Overview

Our CI/CD pipeline comprises several workflows implemented with GitHub Actions:

1. **Continuous Integration (CI)**: Automatically tests, validates, and checks code quality on every push and pull request
2. **Continuous Deployment (CD)**: Automates the release and deployment process
3. **Dependency Updates**: Regularly scans and updates dependencies to maintain security and compatibility

## Continuous Integration

The CI workflow (`ci.yml`) executes on every push to the main branch and on all pull requests, performing:

- **Building**: Verifies the package can be successfully built
- **Linting**: Checks code quality and style with flake8
- **Type Checking**: Validates type hints with mypy
- **Testing**: Runs the entire test suite with pytest
- **Code Coverage**: Measures test coverage and ensures it meets thresholds

### Running the CI Locally

You can run the same CI checks locally before pushing:

```bash
# Linting
flake8 .

# Type checking
mypy --ignore-missing-imports src/

# Tests with coverage
pytest --cov=src tests/
```

## Continuous Deployment

The CD workflow (`cd.yml`) automates the release process when a new version tag (e.g., `v0.1.0`) is pushed:

1. **Build**: Package is built for distribution
2. **Test**: All tests are run against the built package
3. **Publish**: The package is published to PyPI
4. **Release**: A new GitHub release is created with automatically generated changelog

### Creating a New Release

To create a new release:

1. Update version in `src/liquid_energy/__init__.py`
2. Commit changes: `git commit -m "Bump version to X.Y.Z"`
3. Create and push a tag: 
   ```
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

The CD workflow will automatically handle the rest.

## Dependency Updates

The dependency update workflow (`dependency-updates.yml`) runs weekly to check for outdated dependencies:

1. Scans the project for outdated packages
2. Creates a pull request with necessary updates
3. CI tests run on the PR to validate compatibility

## Pull Request Process

All code changes follow this workflow:

1. Create a feature branch from `main`
2. Implement changes following TDD principles
3. Submit a pull request using the PR template
4. Automated CI checks run on the PR
5. Code is reviewed by team members
6. Upon approval and passing checks, PR is merged

## TDD in the CI/CD Process

Our CI/CD enforces the Test-Driven Development (TDD) workflow:

1. **Red Phase**: Tests are written first and verified to fail initially
2. **Green Phase**: Implementation makes the tests pass
3. **Refactor Phase**: Code is improved while maintaining passing tests

The CI pipeline runs tests on every PR and commit, ensuring TDD principles are maintained.

## Code Quality Standards

Our automated checks enforce:

- **Test Coverage**: Minimum 90% code coverage
- **Type Annotations**: All public APIs must have proper type hints
- **Code Style**: Compliant with PEP 8 with minor adjustments (see `setup.cfg`)
- **Documentation**: All modules, classes, and methods must have docstrings

## Branch Protection Rules

The `main` branch is protected with these rules:

1. Pull requests require at least one review
2. All CI checks must pass before merging
3. Branch is protected against force pushes
4. Changes can only be made via pull requests

## CI/CD Maintenance

The CI/CD configuration is stored in:

- `.github/workflows/*.yml`: GitHub Actions workflow definitions
- `setup.cfg`: Configuration for linting, type checking, and test tools
- `requirements.txt`: Dependencies for development and testing

When modifying these files, ensure changes are tested in a separate branch before merging to avoid breaking the pipeline.
