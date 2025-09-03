#!/bin/bash
# Build script for Lambda deployment packages

set -e

echo "🏗️  Building Lambda deployment packages..."
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root (assuming we're in infrastructure/terraform)
PROJECT_ROOT="../.."
TERRAFORM_DIR="."

# Check if we're in the right directory
if [ ! -f "main.tf" ]; then
    echo -e "${RED}❌ Error: Not in terraform directory. Please run from infrastructure/terraform${NC}"
    exit 1
fi

# Create temporary build directory
BUILD_DIR="build_tmp"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

echo -e "${YELLOW}📦 Building Lambda Layer (dependencies)...${NC}"

# Create Lambda Layer
LAYER_DIR="$BUILD_DIR/lambda_layer"
mkdir -p $LAYER_DIR/python

# Install required packages for Lambda (lightweight)
pip install --target $LAYER_DIR/python \
    boto3 \
    botocore \
    pyyaml \
    requests \
    python-dateutil \
    -q

# Remove unnecessary files to reduce size
find $LAYER_DIR -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find $LAYER_DIR -type f -name "*.pyc" -delete 2>/dev/null || true
find $LAYER_DIR -type f -name "*.pyo" -delete 2>/dev/null || true
find $LAYER_DIR -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find $LAYER_DIR -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

# Create layer zip
cd $LAYER_DIR
zip -r ../../lambda_layer.zip . -q -x "*.git*" "*.pyc" "__pycache__/*"
cd ../..

LAYER_SIZE=$(du -h lambda_layer.zip | cut -f1)
echo -e "${GREEN}✅ Lambda Layer created: lambda_layer.zip (${LAYER_SIZE})${NC}"

echo -e "${YELLOW}📦 Building Lambda Deployment Package...${NC}"

# Create Lambda deployment package
LAMBDA_DIR="$BUILD_DIR/lambda_deployment"
mkdir -p $LAMBDA_DIR

# Copy source code
cp -r $PROJECT_ROOT/src $LAMBDA_DIR/
cp -r $PROJECT_ROOT/config $LAMBDA_DIR/ 2>/dev/null || mkdir -p $LAMBDA_DIR/config

# Create placeholder config files if they don't exist
if [ ! -f "$LAMBDA_DIR/config/scheduling_rules.yaml" ]; then
    cp $PROJECT_ROOT/config/scheduling_rules.yaml $LAMBDA_DIR/config/ 2>/dev/null || true
fi

# Create __init__.py files if missing
find $LAMBDA_DIR -type d -exec touch {}/__init__.py \; 2>/dev/null || true

# Remove test files and unnecessary content
find $LAMBDA_DIR -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find $LAMBDA_DIR -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find $LAMBDA_DIR -type f -name "*.pyc" -delete 2>/dev/null || true
find $LAMBDA_DIR -type f -name ".DS_Store" -delete 2>/dev/null || true

# Create deployment zip
cd $LAMBDA_DIR
zip -r ../../lambda_deployment.zip . -q -x "*.git*" "*.pyc" "__pycache__/*" "tests/*"
cd ../..

DEPLOYMENT_SIZE=$(du -h lambda_deployment.zip | cut -f1)
echo -e "${GREEN}✅ Lambda Deployment created: lambda_deployment.zip (${DEPLOYMENT_SIZE})${NC}"

# Clean up
rm -rf $BUILD_DIR

echo -e "${GREEN}🎉 Lambda packages built successfully!${NC}"
echo ""
echo "Files created:"
echo "  - lambda_layer.zip (${LAYER_SIZE})"
echo "  - lambda_deployment.zip (${DEPLOYMENT_SIZE})"
echo ""
echo "Next step: Run 'terraform plan'"
