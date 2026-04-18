# actions/__init__.py
# Import submodules lazily to avoid circular imports during initial module loading

def _load_lb_files():
    """Lazy import to avoid circular dependency issues"""
    try:
        from . import lb_files
    except ImportError as e:
        print(f"⚠️ Could not import lb_files: {e}")

# Avoid forcing imports here to prevent circular-import issues; loader handles registration

# Don't import at module level - let init_loader.py handle it
# _load_lb_files() is only called if needed explicitly

