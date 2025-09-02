# 🌱 Carbon-Aware FinOps - Makefile Commands Guide

This guide provides complete documentation for all Makefile commands in your Carbon-Aware FinOps project.

## 🚀 Quick Reference

| Category | Command | Description |
|----------|---------|-------------|
| **Getting Started** | `make setup` | Complete project setup (run this first!) |
| | `make dev` | Setup development environment |
| | `make fresh-start` | Complete reset + setup + deploy + run (testing) |
| **Development** | `make test` | Run all tests and quality checks |
| | `make clean` | Clean temporary files and caches |
| | `make reset` | Complete project cleanup (⚠️ removes everything!) |
| **Deployment** | `make deploy` | Deploy complete infrastructure to AWS |
| | `make destroy` | Destroy AWS infrastructure (⚠️ careful!) |
| | `make plan` | Show Terraform deployment plan |
| **Operations** | `make run` | Run the complete carbon-aware system |
| | `make dashboard` | Launch real-time dashboard |
| | `make status` | Show system and infrastructure status |
| **Advanced** | `make baseline` | Collect AWS baseline data |
| | `make scheduler` | Run carbon-aware scheduler once |
| | `make rightsizing` | Run rightsizing analysis |
| | `make logs` | View recent Lambda logs |
| | `make instances` | List managed EC2 instances |
| | `make emergency-stop` | Emergency stop all managed instances |
| | `make cleanup-all` | Delete ALL orphaned AWS resources (saves $40+/month!) |

---

## 📋 Essential Commands (Organized by Use Case)

### 🚀 **First Time Setup**
```bash
# 1. Complete project setup
make setup

# 2. Deploy to AWS
make deploy

# 3. Run the system
make run

# 4. View dashboard
make dashboard
```

### 🔄 **Daily Development Workflow**
```bash
# Start development session
make dev

# Run tests before committing
make test

# Clean workspace
make clean
```

### 🧪 **Testing Complete Workflow**
```bash
# Perfect for testing everything from scratch
make fresh-start
# This runs: reset → setup → deploy → run
```

### ☁️ **AWS Infrastructure Management**
```bash
# Preview deployment changes
make plan

# Deploy infrastructure
make deploy

# Check system status
make status

# Destroy infrastructure
make destroy
```

### 🏃 **Running Carbon-Aware Operations**
```bash
# Run complete system
make run

# Run individual components
make baseline      # Collect AWS data
make scheduler     # Run scheduling logic
make rightsizing   # Run rightsizing analysis

# Launch monitoring dashboard
make dashboard
```

---

## 🔧 Detailed Command Reference

### **Setup & Installation**

#### `make setup`
- **Purpose**: Complete project setup for first-time users
- **What it does**:
  - Creates Python virtual environment
  - Installs all dependencies from requirements.txt
  - Installs project in development mode
  - Runs basic health checks
  - Verifies AWS connectivity
- **When to use**: First time running the project
- **Example output**: ✅ Virtual environment created, dependencies installed

#### `make dev`
- **Purpose**: Setup optimized development environment
- **What it does**: Same as setup but optimized for daily development
- **When to use**: Setting up for development work

#### `make fresh-start`
- **Purpose**: Complete workflow testing from clean state
- **What it does**: reset → setup → deploy → run
- **When to use**: Testing complete project workflow
- **⚠️ Warning**: Removes all existing project state

---

### **Development & Testing**

#### `make test`
- **Purpose**: Comprehensive quality checks
- **What it does**:
  - Runs linting (flake8)
  - Runs type checking (mypy)
  - Runs unit tests (pytest)
  - Runs security scan (bandit)
- **When to use**: Before committing code
- **Requirements**: Virtual environment must exist

#### `make clean`
- **Purpose**: Clean temporary files and caches
- **What it does**: Removes __pycache__, .pyc files, test artifacts
- **When to use**: When workspace feels cluttered

#### `make reset`
- **Purpose**: Complete project cleanup
- **What it does**:
  - Removes virtual environment
  - Cleans all Python caches and artifacts
  - Removes Terraform state and cache
  - Removes Lambda deployment files
  - Removes logs and build artifacts
- **⚠️ Warning**: This removes EVERYTHING, requires confirmation

---

### **AWS Infrastructure**

#### `make plan`
- **Purpose**: Preview Terraform deployment changes
- **What it does**: Shows what resources will be created/modified/destroyed
- **When to use**: Before deploying to review changes
- **Output**: Terraform plan showing resource changes

#### `make deploy`
- **Purpose**: Deploy complete infrastructure to AWS
- **What it does**:
  - Initializes Terraform
  - Builds Lambda deployment packages
  - Deploys all AWS resources
  - Sets up secrets in AWS Secrets Manager
- **Resources created**: 40+ AWS resources (~$35/month cost)
- **Time**: ~5-10 minutes

#### `make destroy`
- **Purpose**: Destroy all Terraform-managed AWS resources
- **What it does**: Removes all infrastructure created by Terraform
- **⚠️ Warning**: Permanent deletion, requires 'yes' confirmation
- **Note**: May not remove manually created resources

#### `make status`
- **Purpose**: Show comprehensive system status
- **What it does**:
  - Checks AWS connectivity
  - Shows infrastructure deployment status
  - Lists managed EC2 instances
- **Output**: Status report with ✅/❌/⚠️ indicators

---

### **Operations & Monitoring**

#### `make run`
- **Purpose**: Execute complete carbon-aware system
- **What it does**:
  1. Collects baseline AWS data
  2. Runs scheduling logic
  3. Performs rightsizing analysis
- **When to use**: Execute carbon-aware logic
- **Duration**: ~2-5 minutes depending on instance count

#### `make baseline`
- **Purpose**: Collect AWS baseline data only
- **What it does**: Gathers cost and usage data for 7 days
- **Output**: Saves data to `data/baseline/baseline_data.csv`

#### `make scheduler`
- **Purpose**: Run carbon-aware scheduler once
- **What it does**: 
  - Checks carbon intensity
  - Starts/stops instances based on carbon thresholds
  - Updates DynamoDB state
- **Logic**: Stops instances when carbon intensity > 300 gCO2/kWh

#### `make rightsizing`
- **Purpose**: Run rightsizing analysis
- **What it does**:
  - Analyzes instance utilization
  - Generates rightsizing recommendations
  - Stores recommendations in DynamoDB

#### `make dashboard`
- **Purpose**: Launch real-time monitoring dashboard
- **What it does**: Starts Dash web application
- **Access**: http://localhost:8050
- **Features**: Real-time carbon intensity, cost tracking, instance status

---

### **Monitoring & Debugging**

#### `make logs`
- **Purpose**: View recent Lambda execution logs
- **What it does**: Shows last 1 hour of logs from both Lambda functions
- **Output**: Scheduler and rightsizing Lambda logs

#### `make instances`
- **Purpose**: List all managed EC2 instances
- **What it does**: Shows instance IDs, states, types, schedules, and names
- **Filters**: Only instances tagged with `Project=carbon-aware-finops`

---

### **Emergency Operations**

#### `make emergency-stop`
- **Purpose**: Emergency stop of all managed instances
- **What it does**: Stops (doesn't terminate) all running managed instances
- **Safety**: Requires y/N confirmation
- **When to use**: Emergency situations, high costs, testing

#### `make cleanup-all`
- **Purpose**: Remove ALL orphaned Carbon-Aware FinOps AWS resources
- **💰 Savings**: ~$40-45 per month
- **What it removes**:
  1. Terminates all EC2 instances
  2. Deletes Lambda functions
  3. Deletes DynamoDB tables
  4. Empties and deletes S3 buckets
  5. Deletes CloudWatch log groups
  6. Deletes Secrets Manager secrets
  7. Cleans up IAM roles and security groups
- **⚠️ Warning**: PERMANENT deletion, requires typing 'CLEANUP'
- **When to use**: Clean slate, cost reduction, project cleanup

---

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

# 5. View dashboard
make dashboard
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

### **Complete System Testing**
```bash
# One command to test everything from scratch
make fresh-start

# Manual step-by-step alternative:
make reset    # Complete cleanup
make setup    # Fresh setup  
make deploy   # Deploy infrastructure
make run      # Run system
```

### **Cost Optimization**
```bash
# Check current costs and usage
make status
make instances

# Clean up orphaned resources (saves $40+/month)
make cleanup-all
```

---

## 🚨 Important Notes

### **Before Running Destructive Commands**

**`make reset`:**
- Removes ALL local project state
- Virtual environment will be deleted
- All caches and artifacts will be removed

**`make destroy`:**
- Permanently deletes AWS infrastructure
- Cannot be undone
- Make sure you have backups

**`make cleanup-all`:**
- Permanently deletes ALL project AWS resources
- Will save ~$40-45/month in AWS costs
- Only removes resources tagged with the project

### **AWS Costs**
Current infrastructure deployment creates:
- **EC2 Instances**: ~$30/month (4x t3.micro)
- **Lambda Functions**: ~$0.50/month
- **DynamoDB**: ~$1/month
- **S3 + CloudWatch**: ~$3/month
- **Total**: ~$35/month

### **Configuration**
- **AWS Profile**: `carbon-finops-sandbox` (configurable in Makefile)
- **Region**: `eu-central-1` (configurable in Makefile)
- **Python**: Requires Python 3.9+

---

## 🐛 Troubleshooting

### **Common Issues & Solutions**

**"Virtual environment not found"**
```bash
make setup  # Creates new virtual environment
```

**"AWS connectivity failed"**
```bash
aws configure --profile carbon-finops-sandbox
```

**"Terraform initialization failed"**
```bash
make clean
make deploy
```

**"Tests failing"**
```bash
make test  # Check specific failures and fix reported issues
```

**"High AWS costs"**
```bash
make cleanup-all  # Type 'CLEANUP' when prompted (saves $40+/month)
```

**"Infrastructure stuck during destroy"**
```bash
# Some AWS resources (like EventBridge rules) may need manual cleanup
# Check AWS console and manually delete stuck resources
```

---

## 📚 Additional Resources

- **Show all commands**: `make help`
- **AWS Console**: Monitor resources and costs
- **Dashboard**: http://localhost:8050 (after `make dashboard`)
- **Log Files**: `logs/` directory (after operations)
- **Data Files**: `data/baseline/` and `data/results/`

---

## 🎉 Success Indicators

You know everything is working when:
- ✅ `make setup` completes without errors
- ✅ `make test` shows all quality checks passing  
- ✅ `make deploy` successfully creates 40+ AWS resources
- ✅ `make status` shows infrastructure as deployed
- ✅ `make dashboard` opens the web interface
- ✅ `make run` executes without critical errors

**Happy carbon-aware computing!** 🌱