# Bug Fix: HTTP Server AttributeError

## Issue

When running `repo-explain generate-html`, the server would start but crash when handling HTTP requests with this error:

```python
AttributeError: 'CustomHandler' object has no attribute 'docs_dir'
```

**Location**: `src/repo_explainer/html_generator.py`, line 491

## Root Cause

The bug was in the `DocsServer.start()` method. The nested `CustomHandler` class was trying to access `self.docs_dir`:

```python
class CustomHandler(handler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.docs_dir), **kwargs)  # ❌ Bug
```

**Problem**: `self` in this context refers to the `CustomHandler` instance (the HTTP request handler), not the `DocsServer` instance. The `CustomHandler` doesn't have a `docs_dir` attribute.

## The Fix

Capture `docs_dir` from the outer scope using a closure variable:

```python
def start(self, open_browser: bool = True) -> str:
    # Capture docs_dir in closure for CustomHandler
    docs_dir = self.docs_dir  # ✓ Capture from DocsServer instance
    handler = http.server.SimpleHTTPRequestHandler

    class CustomHandler(handler):
        def __init__(self, *args, **kwargs):
            # Use docs_dir from outer scope
            super().__init__(*args, directory=str(docs_dir), **kwargs)  # ✓ Fixed

        def log_message(self, format, *args):
            # Suppress logs
            pass
```

**Solution**: By assigning `self.docs_dir` to a local variable `docs_dir` before defining the nested class, we create a closure that allows `CustomHandler` to access the directory path from the outer scope.

## Why This Works

### Closure Behavior in Python

When a nested class or function references a variable from an enclosing scope:
1. Python looks for the variable in the local scope first
2. If not found, it looks in the enclosing function's scope (closure)
3. Then global scope, then built-ins

**Before (broken)**:
- `self.docs_dir` → looks for `docs_dir` on the `CustomHandler` instance
- Doesn't exist → `AttributeError`

**After (fixed)**:
- `docs_dir` → looks in local scope (not found)
- Looks in enclosing scope → finds `docs_dir = self.docs_dir`
- Works! ✓

## Testing

Verified the fix with:

```bash
# Test HTML generation (no errors)
repo-explain generate-html example-opencode-md --no-serve
✓ Success

# Test server (responds to requests)
repo-explain generate-html example-opencode-md -p 8888
✓ Server starts
✓ Browser opens
✓ Pages load correctly
✓ No AttributeError
```

## Impact

- ✅ Server now handles HTTP requests correctly
- ✅ Browser can load documentation pages
- ✅ No errors in terminal output
- ✅ All features work as intended

## Prevention

This type of bug occurs when:
1. Nested classes/functions need to access outer instance variables
2. Using `self` inside nested class refers to wrong instance
3. Not using closure variables properly

**Best Practice**: Always capture instance variables in local variables before using them in nested classes:

```python
# Good ✓
outer_var = self.some_attribute
class NestedClass:
    def method(self):
        return outer_var  # Closure variable

# Bad ❌
class NestedClass:
    def method(self):
        return self.some_attribute  # Wrong 'self'
```

## Related Code

File: `src/repo_explainer/html_generator.py`
Class: `DocsServer`
Method: `start()`
Lines: 476-528

## Status

✅ **FIXED** - Server now works correctly with all HTTP requests
