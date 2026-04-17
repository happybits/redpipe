# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RedPipe is a Python library that provides a wrapper around Redis pipelines (redis-py) to make Redis pipelining easier and more efficient. It reduces network round trips when talking to Redis by batching commands together.

## Development Commands

### Testing
- `make test` - Run the full test suite using tox
- `tox` - Run tests across all Python environments (p39,p310,p311,p312 with plain/hiredis variants)
- `python test.py` - Run tests directly
- `tox -e lint` - Run linting and type checking only
- `python -m coverage run --source redpipe -p test.py` - Run tests with coverage

### Linting and Type Checking
- `flake8 --exclude="./build,.venv*,.tox,dist"` - Code linting (configured in tox.ini)
- `mypy redpipe test.py` - Type checking
- Flake8 version: 7.3.0, MyPy version: 1.19.1

### Documentation
- `make documentation` - Build Sphinx documentation
- Documentation is built in `docs/_build/html/`

### Building and Installation
- `make sdist` - Create source distribution
- `make bdist` - Create binary distribution (egg format)
- `make install` - Install package locally
- `make local` - Build extensions in place

### Cleanup
- `make clean` - Remove build artifacts (dist/, build/)
- `make cleancov` - Remove coverage files
- `make cleanmeta` - Remove egg-info files
- `make cleandocs` - Remove documentation build files
- `make cleanall` - Remove all temporary files (combines all clean commands)

### Version Management
- **Current Version**: Located in `redpipe/VERSION` (root `VERSION` is a symlink to this file)
- **Version Bump Process**:
  1. Edit version number in `redpipe/VERSION` (symlink will automatically reflect the change)
  2. Commit with message format: "bump version to X.Y.Z"
  3. setup.py automatically reads version from `redpipe/VERSION` at build time

## Code Architecture

### Core Components

**Connection Management** (`redpipe/connections.py`)
- Singleton-based connection manager supporting named connections
- Use `redpipe.connect_redis(client)` to bind Redis client
- Supports multiple Redis instances with named connections

**Pipeline System** (`redpipe/pipelines.py`)
- Two-tier pipeline system:
  - `Pipeline` class: Executor that manages Redis commands
  - `NestedPipeline` class: Command aggregator for nested operations
- Usage pattern: `with redpipe.pipeline() as pipe:`

**Keyspace Abstractions** (`redpipe/keyspaces.py`)
- Object-oriented interfaces for Redis data structures
- Classes: Hash, Set, List, SortedSet, String, etc.
- Provides high-level operations on Redis keys

**Field System** (`redpipe/fields.py`)
- Type-safe field definitions for data serialization/deserialization
- Field types: IntegerField, FloatField, TextField, AsciiField, etc.

**Future Objects** (`redpipe/futures.py`)
- Deferred execution results resolved after pipeline execution
- Allows assignment of pipeline results to variables before execution

### Redis Cluster Support
- Built-in support for Redis Cluster deployments (`redpipe/redis_cluster.py`)
- Handles cluster topology and node distribution

## Testing Structure

**Main Test File**: `test.py` - Comprehensive test suite in a single file
**Test Configuration**: `conftest.py` - pytest configuration with custom port option
**Benchmarking**: `bench.py` - Performance benchmarks

## Package Information

- **Version**: Located in `redpipe/VERSION`
- **Dependencies**: `redis>=5.0.0` (see requirements.txt)
- **Dev Dependencies**: coverage, redislite>=3.0.271, flake8, mypy, types-redis
- **Python Support**: 3.9+ with full Python 3.12 compatibility (see setup.py)
- **License**: MIT

## Development Notes

- Tests use `redislite` for embedded Redis testing
- Tox configuration supports both plain and hiredis environments
- Documentation uses Sphinx with reStructuredText format
- Code follows PEP 8 style guidelines enforced by flake8
- Type hints are checked with mypy