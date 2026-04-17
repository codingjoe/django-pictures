# Contributing

When writing code, you MUST ALWAYS follow the [naming-things](https://github.com/codingjoe/naming-things/blob/main/README.md) guidelines.

<!--
Bots/Agents MUST use:
curl -sSL https://raw.githubusercontent.com/codingjoe/naming-things/refs/heads/main/README.md
-->

To run the tests, use the following command:

```bash
uv run pytest
```

Benchmarking snapshots are created automatically.
To compare your feature branch against the main branch,
run the test suite on main, followed by:

```
uv run pytest --benchmark-compare
```

Before your first commit, ensure that the pre-commit hooks are installed by running:

```bash
uv pre-commit install
```

## Testing with Extra Dependencies

```bash
export REDIS_URL=redis://localhost:6379
uv run --extra=dramatiq pytest
uv run --extra=celery pytest
uv run --extra=django-rq pytest
uv run --extra=drf pytest
uv run --extra=cleanup pytest
```
