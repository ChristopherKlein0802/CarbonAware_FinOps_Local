# 🌱 Carbon-Aware FinOps - Essential Commands Guide

This guide provides complete documentation for the streamlined Makefile commands in your Carbon-Aware FinOps project.

## 🚀 Quick Reference

| Category | Command | Description |
|----------|---------|-------------|
| **Getting Started** | `make setup` | Complete project setup (run this first!) |
| **Development** | `make test` | Run comprehensive tests and quality checks |
| | `make cleanup` | Clean temporary files and caches |
| | `make reset` | Complete project cleanup (⚠️ removes everything!) |
| **Deployment** | `make deploy` | Deploy complete infrastructure to AWS |
| | `make destroy` | Destroy AWS infrastructure (⚠️ careful!) |
| **Operations** | `make run` | Run the complete carbon-aware system |
| | `make dashboard` | Launch real-time dashboard |
| | `make status` | Show comprehensive system status |
| **Utilities** | `make emergency-stop` | Emergency stop all managed instances |
| | `make logs` | View recent Lambda logs |
| | `make instances` | List managed EC2 instances |

---

## 🔧 Essential Command Details

### 🚀 Getting Started Commands

#### `make setup`
- **Purpose**: Complete project setup for first-time users
- **What it does**: 
  - Creates Python virtual environment
  - Installs all dependencies
  - Runs quality checks
  - Verifies AWS connectivity
- **When to use**: Run this first when setting up the project
- **Example**:
```bash
make setup
```

### 💻 Development Commands

#### `make test`
- **Purpose**: Run comprehensive quality checks
- **What it does**:
  - Lints code with flake8
  - Type checks with mypy
  - Runs pytest tests
  - Security scan with bandit
- **When to use**: Before committing code changes
- **Example**:
```bash
make test
```

#### `make cleanup`
- **Purpose**: Clean temporary files and caches
- **What it does**:
  - Removes Python cache files
  - Cleans pytest cache
  - Removes build artifacts
  - Deletes system files like .DS_Store
- **When to use**: To clean up development environment
- **Example**:
```bash
make cleanup
```

#### `make reset`
- **Purpose**: Complete project reset (nuclear option!)
- **What it does**:
  - Removes virtual environment
  - Cleans all cache files
  - Removes Terraform state
  - Deletes Lambda packages
  - Cleans logs and build artifacts
- **When to use**: When you want to start fresh
- **⚠️ Warning**: This removes everything - use with caution!
- **Example**:
```bash
make reset
# Type 'y' when prompted to confirm
```

### ☁️ Deployment Commands

#### `make deploy`
- **Purpose**: Deploy complete infrastructure to AWS
- **What it does**:
  1. Initializes Terraform
  2. Builds Lambda packages
  3. Deploys infrastructure
  4. Sets up secrets
- **Prerequisites**: AWS SSO configured and logged in
- **Example**:
```bash
make deploy
```

#### `make destroy`
- **Purpose**: Completely destroy AWS infrastructure
- **What it does**:
  - Shows current resources
  - Uses terraform destroy
  - Cleans orphaned resources
  - Verifies complete cleanup
- **⚠️ Warning**: This permanently deletes ALL AWS resources!
- **Example**:
```bash
make destroy
# Type 'CLEANUP' when prompted to confirm
```

### 🏃 Operations Commands

#### `make run`
- **Purpose**: Run the complete carbon-aware system
- **What it does**:
  1. Triggers Lambda carbon-aware scheduler
  2. Checks Lambda execution results
  3. Shows system status
- **Prerequisites**: Infrastructure must be deployed
- **Example**:
```bash
make run
```

#### `make dashboard`
- **Purpose**: Launch real-time dashboard
- **What it does**: Starts Flask dashboard at http://localhost:8050
- **When to use**: To view real-time metrics and system status
- **Example**:
```bash
make dashboard
# Press Ctrl+C to stop
```

#### `make status`
- **Purpose**: Show comprehensive system status
- **What it displays**:
  - AWS connection status
  - Terraform resource count
  - EC2 instance states
  - Lambda function status
- **Example**:
```bash
make status
```

### 🔧 Utility Commands

#### `make emergency-stop`
- **Purpose**: Emergency stop all managed instances
- **What it does**: Immediately stops ALL running EC2 instances with the project tag
- **When to use**: Emergency situations to reduce costs
- **⚠️ Warning**: This stops instances immediately!
- **Example**:
```bash
make emergency-stop
# Type 'y' when prompted to confirm
```

#### `make logs`
- **Purpose**: View recent Lambda function logs
- **What it shows**: Recent logs from scheduler Lambda function
- **When to use**: For debugging and monitoring
- **Example**:
```bash
make logs
```

#### `make instances`
- **Purpose**: List all managed EC2 instances
- **What it shows**: Instance ID, type, state, and name in table format
- **When to use**: To check instance status
- **Example**:
```bash
make instances
```

---

## 📋 Common Workflows

### 🌟 First Time Setup
```bash
# 1. Setup project
make setup

# 2. Deploy infrastructure  
make deploy

# 3. Run the system
make run

# 4. View dashboard
make dashboard
```

### 🔄 Daily Development
```bash
# Run tests before committing
make test

# Clean up temporary files
make cleanup

# Check system status
make status
```

### 🚨 Emergency Procedures
```bash
# Stop all instances immediately
make emergency-stop

# Check what's running
make instances

# View recent logs
make logs
```

### 🧹 Complete Cleanup
```bash
# Destroy AWS infrastructure (saves money)
make destroy

# Reset local project (optional)
make reset
```

---

## 🔧 Configuration

The Makefile uses these default configurations:
- **AWS Profile**: `carbon-finops-sandbox`
- **AWS Region**: `eu-central-1`
- **Python**: `python3`
- **Virtual Environment**: `venv/`

To customize, edit the configuration variables at the top of the Makefile:
```makefile
AWS_PROFILE := your-profile-name
AWS_REGION := your-preferred-region
```

---

## 🆘 Troubleshooting

### Common Issues

**Virtual environment not found**:
```bash
make setup  # Run this first
```

**AWS authentication failed**:
```bash
aws sso login --profile carbon-finops-sandbox
```

**Terraform state locked**:
```bash
# Check for running processes, then try again
make destroy
```

**No instances found**:
```bash
# Deploy infrastructure first
make deploy
```

---

## 💡 Tips

- Always run `make status` to check system health
- Use `make emergency-stop` if you see unexpected costs
- Run `make test` before making changes
- Use `make destroy` to completely clean up AWS resources when done
- Check `make logs` if something isn't working as expected

The streamlined Makefile focuses on essential commands only, making it easier to understand and use the Carbon-Aware FinOps system!