#!/bin/bash
# Setup script for Carbon-Aware FinOps environment

set -e

echo "🌱 Carbon-Aware FinOps Environment Setup"
echo "========================================"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

echo "✅ AWS CLI found"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws sso login --sso-session carbon-finops-sandbox' first."
    exit 1
fi

echo "✅ AWS credentials configured"

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p data/baseline data/results data/reports logs

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your API keys"
echo "2. Deploy infrastructure: cd infrastructure/terraform && terraform init"
echo "3. Run baseline collection: python scripts/collect_baseline.py"
echo ""
echo "For more information, visit the project documentation."