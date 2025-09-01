# 🌱 Carbon-Aware FinOps - Makefile Usage Guide

This guide explains how to use the streamlined Makefile for efficient development and deployment of your Carbon-Aware FinOps project.

## 🚀 Quick Start

### First Time Setup
```bash
# 1. Clone the repository and navigate to it
cd CarbonAware_FinOps_Local

# 2. Run complete project setup
make setup

# 3. Deploy infrastructure to AWS
make deploy

# 4. Run the carbon-aware system
make run
```

### Daily Development Workflow
```bash
# Start development session
make dev

# Run tests before committing
make test

# Clean up temporary files
make clean
```

### Complete Testing Workflow
```bash
# Test everything from scratch (perfect for thorough testing!)
make fresh-start

# Or step-by-step:
make reset    # Complete cleanup
make setup    # Fresh setup  
make deploy   # Deploy infrastructure
make run      # Run system
```

## 📋 Essential Commands

### 🔧 **Setup & Installation**

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make setup` | Complete project setup | ✅ **First time** running the project |
| `make dev` | Development environment | 🔄 Setting up for development |
| `make fresh-start` | Complete reset + setup + deploy + run | 🧪 **Perfect for testing everything from scratch** |

**Example:**
```bash
# First time setup
make setup
# ✅ Creates virtual environment
# ✅ Installs all dependencies  
# ✅ Runs basic health checks
# ✅ Verifies AWS connectivity
```

### 💻 **Development**

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make test` | Run all quality checks | 🧪 Before committing code |
| `make clean` | Clean temporary files | 🧹 When workspace feels cluttered |

**Example:**
```bash
# Before committing changes
make test
# ✅ Runs linting (flake8)
# ✅ Runs type checking (mypy)  
# ✅ Runs unit tests (pytest)
# ✅ Runs security scan (bandit)
```

### ☁️ **Deployment**

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make deploy` | Deploy to AWS | 🚀 Deploy infrastructure |
| `make destroy` | Destroy AWS resources | ⚠️ Clean up (CAREFUL!) |
| `make plan` | Show deployment plan | 👀 Preview changes |

**Example:**
```bash
# Deploy complete infrastructure
make deploy
# ✅ Initializes Terraform
# ✅ Builds Lambda packages
# ✅ Deploys infrastructure
# ✅ Sets up secrets
```

### 🏃 **Operations**

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make run` | Run complete system | 🏃 Execute carbon-aware logic |
| `make dashboard` | Launch dashboard | 📊 View real-time metrics |
| `make status` | Show system status | 📈 Check system health |

**Example:**
```bash
# Run the carbon-aware system
make run
# ✅ Collects baseline AWS data
# ✅ Runs scheduling logic
# ✅ Performs rightsizing analysis

# View real-time dashboard
make dashboard
# 🌐 Opens dashboard at http://localhost:8050
```

## 🎯 Common Workflows

### **New Developer Onboarding**
```bash
# 1. Initial setup
make setup

# 2. Verify everything works
make test

# 3. Deploy infrastructure
make deploy

# 4. Run system once to verify
make run
```

### **Daily Development**
```bash
# 1. Start development
make dev

# 2. Make your changes...

# 3. Test before committing
make test

# 4. Deploy if needed
make deploy
```

### **Production Deployment**
```bash
# 1. Clean workspace
make clean

# 2. Run full tests
make test

# 3. Review deployment plan
make plan

# 4. Deploy to production
make deploy

# 5. Verify deployment
make status
```

### **Troubleshooting**
```bash
# Check system health
make status

# View recent logs
make logs

# List managed instances
make instances

# Emergency stop (if needed)
make emergency-stop
```

## 🔧 Advanced Commands

### **Individual Components**
```bash
make baseline     # Collect AWS baseline data only
make scheduler    # Run scheduler logic once
make rightsizing  # Run rightsizing analysis once
```

### **Monitoring & Debugging**
```bash
make logs         # View Lambda logs
make instances    # List managed EC2 instances
make status       # Comprehensive status check
```

### **Emergency Operations**
```bash
make emergency-stop  # Stop all managed instances
make destroy        # Destroy all infrastructure
```

## ⚙️ Configuration

### **AWS Profile Configuration**
The Makefile uses the `carbon-finops-sandbox` AWS profile by default. To configure:

```bash
# Configure AWS profile
aws configure --profile carbon-finops-sandbox

# Or set different profile in Makefile
# Change: AWS_PROFILE := your-profile-name
```

### **Region Configuration**
Default region is `eu-central-1`. To change:
```bash
# Edit Makefile line:
# AWS_REGION := your-preferred-region
```

## 🚨 Important Notes

### **Before Running `make destroy`**
- ⚠️ **This permanently deletes all AWS resources**
- ⚠️ **This cannot be undone**  
- ⚠️ **Make sure you have backups of important data**

### **AWS Costs**
The infrastructure deployment creates AWS resources that incur costs:
- 4x t3.micro instances: ~$30/month
- Lambda executions: ~$0.50/month
- DynamoDB + S3 + CloudWatch: ~$4/month
- **Total: ~$35/month**

### **Security**
- Never commit AWS credentials
- Use AWS profiles for authentication
- Regularly rotate API keys
- Monitor AWS usage and costs

## 🐛 Troubleshooting

### **Common Issues**

**"Virtual environment not found"**
```bash
# Solution: Run setup first
make setup
```

**"AWS connectivity failed"**
```bash
# Solution: Configure AWS profile
aws configure --profile carbon-finops-sandbox
```

**"Terraform initialization failed"**
```bash
# Solution: Clean and retry
make clean
make deploy
```

**"Tests failing"**
```bash
# Solution: Check specific failures
make test
# Then fix reported issues
```

### **Getting Help**
```bash
# Show all available commands
make help

# Show detailed command descriptions  
make
```

## 📚 Next Steps

After successfully running the Makefile commands:

1. **Explore the Dashboard**: `make dashboard` - View real-time carbon intensity data
2. **Monitor Logs**: `make logs` - Check Lambda execution logs  
3. **Review Costs**: Check AWS billing dashboard
4. **Customize Scheduling**: Edit `config/scheduling_rules.yaml`
5. **Add More Instances**: Tag EC2 instances with `Project=carbon-aware-finops`

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ `make setup` completes without errors
- ✅ `make test` shows all quality checks passing
- ✅ `make deploy` successfully creates AWS resources
- ✅ `make status` shows infrastructure as deployed
- ✅ `make dashboard` opens the web interface
- ✅ `make run` executes without critical errors

Happy carbon-aware computing! 🌱