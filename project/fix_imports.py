import os

# Create __init__.py files
init_files = [
    'utils/__init__.py',
    'database/__init__.py',
    'services/__init__.py', 
    'services/user_service/__init__.py',
    'services/bank_service/__init__.py',
    'services/stock_exchange_service/__init__.py',
    'services/trade_logger_service/__init__.py'
]

for init_file in init_files:
    os.makedirs(os.path.dirname(init_file), exist_ok=True)
    with open(init_file, 'w') as f:
        f.write('# Python package marker\n')
    print(f"Created {init_file}")

print("All __init__.py files created!")