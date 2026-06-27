import os
import importlib

def import_all_models():
    """Dynamically imports all Python files inside app/models/"""
    # 1. This file is at backend/app/models/__init__.py
    current_file_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Path to the actual app directory is one level up (backend/app)
    app_path = os.path.dirname(current_file_dir)

    # 3. Path to the models directory is current_file_dir itself (backend/app/models)
    models_path = current_file_dir

    if not os.path.exists(models_path):
        print(f"Warning: Models directory not found at {models_path}")
        return

    # 4. List all files directly in the models directory
    for file in os.listdir(models_path):
        # Target only Python files, excluding __init__.py
        if file.endswith(".py") and file != "__init__.py":
            # Strip the ".py" extension
            file_name_without_ext = file[:-3]

            # Build complete module path (e.g., app.models.user)
            module_name = f"app.models.{file_name_without_ext}"

            try:
                importlib.import_module(module_name)
                print(f"Successfully auto-discovered model: {module_name}")
            except ImportError as e:
                print(f"Warning: Could not dynamically import {module_name}: {e}")
