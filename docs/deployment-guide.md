# Universal Deployment Guide

## Overview
This Carbon-Aware FinOps tool can now be deployed to **any AWS account** and will automatically analyze **ALL EC2 instances** in that account, providing cost and carbon emission insights.

## Features
- ✅ **Universal Account Support**: Deploy to any AWS account with proper permissions
- ✅ **SSO Login Support**: Works with AWS SSO profiles
- ✅ **All Instance Analysis**: Analyzes ALL instances in account (not just tagged test instances)
- ✅ **German Grid Focus**: Optimized for German electricity grid data
- ✅ **Auto-Generated Naming**: Project names generated from account ID
- ✅ **Real Cost Data**: Uses AWS Cost Explorer for accurate cost data
- ✅ **Carbon-Aware Optimization**: Shows scheduling impact on both cost and emissions

## Quick Start

### 1. Prerequisites
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Terraform
brew install terraform  # macOS
# or download from https://terraform.io

# Get ElectricityMap API key (optional but recommended)
# Sign up at: https://portal.electricitymaps.com/
```

### 2. Authentication Setup

#### For SSO Users:
```bash
# Configure SSO profile
aws configure sso --profile your-company-sso

# Login before deployment
aws sso login --profile your-company-sso
export AWS_PROFILE=your-company-sso
```

#### For Regular AWS Credentials:
```bash
aws configure --profile your-profile
export AWS_PROFILE=your-profile
```

### 3. Deploy to Any Account

```bash
# Set your API key (optional)
export ELECTRICITYMAP_API_KEY=your-api-key-here

# Set AWS profile
export AWS_PROFILE=your-profile-name

# Deploy (automatically detects account and region)
./deploy_universal.sh
```

### 4. View Results

After deployment (wait 1-2 hours for initial data):
```bash
# Start dashboard
make dashboard

# Or run improved dashboard
python3 improved_thesis_dashboard.py
```

Access at: http://localhost:8050

## Configuration Options

### Environment Variables
```bash
export AWS_PROFILE=your-profile          # AWS profile to use
export AWS_REGION=eu-central-1           # Target region (default)
export ELECTRICITYMAP_API_KEY=your-key   # API key for carbon data
```

### Supported Regions
Focus on German/European regions for accurate carbon data:
- `eu-central-1` (Frankfurt) - **Recommended**
- `eu-central-2` (Zurich)
- `eu-west-1` (Ireland)
- `eu-west-2` (London)
- `eu-west-3` (Paris)

### Instance Optimization Tags

The tool analyzes ALL instances by default. To enable scheduling optimization, tag instances:

```bash
# Office hours scheduling (Mon-Fri 8-18)
aws ec2 create-tags --resources i-1234567890abcdef0 --tags Key=ScheduleType,Value=office-hours

# Weekdays only (Mon-Fri 24h)
aws ec2 create-tags --resources i-1234567890abcdef0 --tags Key=ScheduleType,Value=weekdays-only

# Carbon-aware scheduling (stops during high emissions)
aws ec2 create-tags --resources i-1234567890abcdef0 --tags Key=ScheduleType,Value=carbon-aware
```

## What Gets Deployed

### Core Infrastructure:
- **Lambda Function**: Analyzes all instances hourly
- **DynamoDB Table**: Stores cost and carbon analysis results
- **EventBridge Rule**: Triggers analysis every hour
- **IAM Roles**: Minimal permissions for analysis only

### Optional Test Infrastructure (testing mode):
- VPC, Subnet, Security Group
- 4 test EC2 instances with different scheduling patterns

## Deployment Modes

### Universal Mode (Default)
- Analyzes **ALL instances** in the account
- No test instances created
- Minimal infrastructure footprint
- Production-ready for any AWS account

### Testing Mode
- Creates test instances for demonstration
- Only analyzes tagged test instances
- Useful for development and research

To use testing mode:
```bash
export DEPLOYMENT_MODE=testing
./deploy_universal.sh
```

## Security & Permissions

### Required IAM Permissions:
- `ec2:DescribeInstances` - Read instance information
- `ce:GetCostAndUsage` - Read cost data from Cost Explorer
- `dynamodb:*` - Store analysis results
- `cloudwatch:PutMetricData` - Send custom metrics
- `lambda:*` - Lambda function management

### Data Privacy:
- Only reads metadata and costs
- No access to instance internals
- All data stays within your AWS account
- No external data transmission except API calls to ElectricityMap

## Thesis Research Benefits

This universal deployment enables:

1. **Real-World Analysis**: Analyze actual production workloads
2. **Cost Validation**: Use real AWS billing data
3. **Regional Comparison**: Deploy in different regions for comparison
4. **Tool Benchmarking**: Compare against other FinOps tools
5. **Carbon Impact**: Quantify environmental impact of scheduling

## Troubleshooting

### Common Issues:

1. **SSO Token Expired**
   ```bash
   aws sso login --profile your-profile
   ```

2. **No Cost Data**
   - Cost Explorer has 24-hour delay for new instances
   - Ensure account has EC2 usage for cost analysis

3. **No Carbon Data**
   - Check ELECTRICITYMAP_API_KEY is set
   - Verify API key is valid at portal.electricitymaps.com

4. **Permission Denied**
   - Ensure IAM user/role has required permissions
   - Check AWS account limits

### Get Help:
```bash
# Check deployment status
terraform output

# View Lambda logs
aws logs tail /aws/lambda/carbon-finops-123456-carbon-scheduler --follow

# Check DynamoDB data
aws dynamodb scan --table-name carbon-finops-123456-results --max-items 5
```

## Next Steps

1. **Deploy to multiple accounts** for comparative analysis
2. **Tag instances** with optimization strategies
3. **Compare results** with traditional cost-only tools
4. **Document findings** for thesis research
5. **Scale analysis** across different regions and workloads