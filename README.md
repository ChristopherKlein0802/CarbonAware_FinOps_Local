# Carbon-Aware FinOps Framework

## Overview
This project implements a Carbon-Aware FinOps framework that demonstrates how organizations can achieve sustainability goals while optimizing cloud costs through automated interventions on AWS EC2 instances.

### Key Features
- 🌱 Carbon-aware instance scheduling
- 💰 Cost optimization through off-hours automation
- 📊 Unified cost and carbon reporting
- 🔄 Automated right-sizing recommendations
- 📈 Real-time carbon intensity tracking

## Project Structure
- `infrastructure/` - Terraform and CloudFormation templates
- `src/` - Core application code
- `tests/` - Unit and integration tests
- `scripts/` - Deployment and utility scripts
- `config/` - Configuration files
- `data/` - Data storage for baseline and results
- `docs/` - Documentation

## Prerequisites
- AWS Account with appropriate permissions
- Python 3.9+
- Terraform 1.0+
- AWS CLI configured
- API keys for carbon intensity data (WattTime or electricityMap)

## Quick Start

1. Clone the repository
```bash
git clone https://github.com/ChristopherKlein0802/CarbonAware_FinOps_Local.git
cd CarbonAware_FinOps_Local