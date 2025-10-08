# 👤 User Documentation

This directory contains user-facing documentation including user guides, developer handbooks, and integration testing plans.

## 📁 Contents

- [**user-guide.md**](user-guide.md) - End-user guide for using the Carbon-Aware FinOps Dashboard
- [**developer-handbook.md**](developer-handbook.md) - Developer guide for extending and maintaining the system
- [**integration-testing-plan.md**](integration-testing-plan.md) - Integration testing approach and test cases

## 🎯 Purpose

The user documentation provides:

- **Usage Instructions:** How to set up, configure, and use the dashboard
- **Developer Guidance:** How to extend functionality and add new features
- **Testing Procedures:** How to test integrations with AWS, Boavizta, ElectricityMaps

## 👥 Target Audiences

### End Users (DevOps, FinOps Teams)
- **Focus:** Dashboard navigation, metric interpretation, business insights
- **See:** [user-guide.md](user-guide.md)

### Developers (System Maintainers)
- **Focus:** Code architecture, extension points, contribution guidelines
- **See:** [developer-handbook.md](developer-handbook.md)

### QA Engineers (Testers)
- **Focus:** Integration testing, API mocking, validation procedures
- **See:** [integration-testing-plan.md](integration-testing-plan.md)

## 🚀 Quick Start

1. **Prerequisites:** AWS SSO credentials, Python 3.11+, API keys configured
2. **Installation:** `make install` or `pip install -r requirements.txt`
3. **Configuration:** Copy `.env.example` to `.env` and configure API keys
4. **Launch:** `make run` or `streamlit run src/app.py`

## 🔗 Related Documentation

- [Architecture (docs/architecture/)](../architecture/) - System design and structure
- [Development (docs/development/)](../development/) - Development practices and test coverage
- [Main README](../../README.md) - Project overview and quick reference

---

**For end users:** Start with [user-guide.md](user-guide.md).
**For developers:** Start with [developer-handbook.md](developer-handbook.md).
