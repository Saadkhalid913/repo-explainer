# HTML Generator

**Type**: `module`  
**ID**: `html-generator`  
**Location**: `src/repo_explainer/html_generator.py:1-852`  

## Overview

Converts markdown documentation to HTML with navigation, update banners, and a history page.

## Key Functions

### `generate`

**Location**: `src/repo_explainer/html_generator.py:189-238`  
**Signature**:  
```
def generate(self)
```

Converts markdown files to styled HTML and generates history pages.

### `_get_update_banner_html`

**Location**: `src/repo_explainer/html_generator.py:43-99`  
**Signature**:  
```
def _get_update_banner_html(self, root_path)
```

Generates a notification banner for recent documentation updates.

## Dependencies

### External Dependencies

- `markdown`
- `rich`

## Used By

This component is used by:

- [`CLI Module`](cli.md)

---

_Generated from component analysis_
