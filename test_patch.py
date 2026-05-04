import pkgutil
import sys

print(f"Before patch, hasattr(pkgutil, 'find_loader'): {hasattr(pkgutil, 'find_loader')}")

if not hasattr(pkgutil, "find_loader"):
    from importlib.util import find_spec
    def find_loader(name):
        spec = find_spec(name)
        return spec.loader if spec else None
    pkgutil.find_loader = find_loader

print(f"After patch, hasattr(pkgutil, 'find_loader'): {hasattr(pkgutil, 'find_loader')}")
print(f"pkgutil.find_loader('os'): {pkgutil.find_loader('os')}")

import dash
print(f"After importing dash, hasattr(pkgutil, 'find_loader'): {hasattr(pkgutil, 'find_loader')}")
