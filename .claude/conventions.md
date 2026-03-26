# Conventions

## Config pattern

Global defaults live in `.env` / `Config` (dataclass with `os.getenv` defaults). Per-project overrides are optional fields in `ProjectConfig` (all `None` by default). Resolution uses `project_value or env_value` — never merge or deep-copy.

## Adding a new render setting

1. Add the field to `Config` in `config.py` with an `os.getenv` default.
2. Add an optional `field | None` to `ProjectConfig` in `project.py`.
3. Add `raw.get("field")` to the `ProjectConfig(...)` constructor call in `load_project`.
4. Resolve it at the top of `render_thumbnail` with `project_config.field or env_config.field`.
5. Document the new key in `.env.example` and `README.md`.

## Render helpers

Private helpers in `render.py` are prefixed with `_` and take only PIL `Image` objects plus primitive config values — no `Config` or `ProjectConfig` objects. This keeps them unit-testable in isolation.

## Image handling

All images are opened and worked on in `RGBA` mode. The final canvas is converted to `RGB` before saving as PNG.

## CLI output

Use `click.echo` for stdout, `click.echo(..., err=True)` for errors. The `batch` command continues on per-project errors — never raise from inside the loop.
