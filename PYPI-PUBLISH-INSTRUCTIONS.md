# PyPI Publish Instructions for 0latency-cli

## Prerequisites

1. PyPI account at https://pypi.org
2. API token from https://pypi.org/manage/account/token/
3. twine installed: pip install twine

## Pre-publish Checklist

- [x] Version bumped in pyproject.toml (currently 0.1.0)
- [x] README.md is up to date
- [x] Build artifacts generated (dist/ directory)
- [x] twine check dist/* passes (PASSED)
- [x] Git tag pushed to GitHub (git push origin v0.1.0)
- [x] GitHub release created

## Publish to PyPI

### Step 1: Set PyPI Token

Export your PyPI API token as an environment variable:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR_TOKEN_HERE
```

Or create ~/.pypirc:

```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

**IMPORTANT:** Never commit your PyPI token to git!

### Step 2: Upload to PyPI

```bash
cd /root/0latency-cli
twine upload dist/*
```

This will:
1. Upload 0latency_cli-0.1.0-py3-none-any.whl
2. Upload 0latency_cli-0.1.0.tar.gz
3. Make the package available at https://pypi.org/project/0latency-cli/

### Step 3: Verify

After upload, verify the package page:

- PyPI project page: https://pypi.org/project/0latency-cli/
- Test installation: pip install 0latency-cli==0.1.0
- Check README renders correctly on PyPI

## Test PyPI (Optional)

To test the upload process without publishing to production PyPI:

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ 0latency-cli
```

## Troubleshooting

### Upload fails with "403 Forbidden"
- Verify your API token is correct
- Check token has upload permissions

### Upload fails with "400 File already exists"
- Version 0.1.0 already published - PyPI does not allow re-uploads
- Bump version in pyproject.toml, rebuild, and try again

### README does not render on PyPI
- Ensure readme = "README.md" in pyproject.toml
- Verify README is valid Markdown
- Check for unsupported GitHub-specific features

## Current Build Status

**Safe to paste: YES** (no secrets in output below)

```
Build artifacts in dist/:
- 0latency_cli-0.1.0-py3-none-any.whl (18K)
- 0latency_cli-0.1.0.tar.gz (24K)

Twine validation: PASSED
```

Ready for PyPI upload once you have your API token configured.
