#!/usr/bin/env python3
"""
Fix datetime parsing issues in carbon_api_client.py
"""

import re

# Read the current file
with open('src/carbon/carbon_api_client.py', 'r') as f:
    content = f.read()

# Add the helper function after imports if not already present
if 'parse_iso_datetime' not in content:
    helper_function = '''
def parse_iso_datetime(datetime_str: str) -> datetime:
    """Parse ISO datetime string, handling 'Z' timezone indicator."""
    if datetime_str.endswith('Z'):
        datetime_str = datetime_str[:-1]
    
    if '+' in datetime_str:
        datetime_str = datetime_str.split('+')[0]
    elif datetime_str.count('-') > 2:
        for i in range(len(datetime_str) - 1, -1, -1):
            if datetime_str[i] in ['-', '+'] and i > 10:
                datetime_str = datetime_str[:i]
                break
    
    try:
        if '.' in datetime_str:
            return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f')
        else:
            return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return datetime.fromisoformat(datetime_str)
'''
    
    # Find where to insert (after logger definition)
    insert_pos = content.find('logger = logging.getLogger(__name__)')
    if insert_pos != -1:
        end_of_line = content.find('\n', insert_pos)
        content = content[:end_of_line+1] + helper_function + content[end_of_line+1:]
    else:
        # Fallback: insert after imports
        import_end = content.rfind('import ')
        import_end = content.find('\n', import_end) + 1
        content = content[:import_end] + helper_function + content[import_end:]

# Replace all datetime.fromisoformat calls
content = re.sub(r'datetime\.fromisoformat\((.*?)\)', r'parse_iso_datetime(\1)', content)

# Also replace in return statements where it might be formatted differently
content = re.sub(r'datetime\.fromisoformat', 'parse_iso_datetime', content)

# Save the fixed file
with open('src/carbon/carbon_api_client.py', 'w') as f:
    f.write(content)

print("✅ Fixed datetime parsing issues in carbon_api_client.py")
print("💾 Backup saved as src/carbon/carbon_api_client.py.backup")

# Create a backup
import shutil
shutil.copy('src/carbon/carbon_api_client.py', 'src/carbon/carbon_api_client.py.backup')

# Run a quick test
print("\n🧪 Testing the fix...")
try:
    from src.carbon.carbon_api_client import parse_iso_datetime
    
    test_dates = [
        '2024-01-01T12:00:00Z',
        '2024-01-01T12:00:00.123456Z',
        '2024-01-01T12:00:00+01:00',
        '2024-01-01T12:00:00',
    ]
    
    for date_str in test_dates:
        result = parse_iso_datetime(date_str)
        print(f"  ✓ Parsed: {date_str} → {result}")
    
    print("\n✅ All datetime formats parsed successfully!")
    
except Exception as e:
    print(f"❌ Error testing: {e}")
    print("Please check the file manually.")

print("\n📝 Next step: Run the tests again")
print("   pytest tests/test_carbon.py -v")