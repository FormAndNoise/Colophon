# AUDIT-03 — Security and Configuration Audit

Scope: tracked files in `ComfyUI-Book-Tools` at audit branch `wt/t_eb89a37f`, including git history and all Python nodes. The package is a local ComfyUI custom-node plugin; it does not expose HTTP routes, sessions, JWTs, CORS configuration, SQL, shell commands, or browser rendering.

## Severity-ranked findings

| Severity | Location | Issue / impact | Remediation | Status |
|---|---|---|---|---|
| Medium | `nodes/core_controls.py:329-390` | Font download accepted a URL parsed from remote CSS without an allowlist or request time/size limits. A compromised/intercepted CSS response could redirect the node to an arbitrary host and cause an unbounded request/write. | Require HTTPS `fonts.gstatic.com`, add connect/read timeouts, and reject payloads over 20 MiB. | **Fixed in this branch** |
| Medium | `nodes/core_controls.py:339` | `font_name` was used as a mapping key without explicit validation. Normal ComfyUI controls constrain this value, but direct/API invocation could raise an uncontrolled `KeyError`. | Validate against the supported-font mapping before constructing paths. | **Fixed in this branch** |
| Low | `nodes/core_controls.py:334`, `nodes/front_matter.py:41,62`, `nodes/text_to_image.py:71` | Several UI defaults are Windows- or Linux-specific absolute font paths. A default can silently fall back or fail on another OS, making workflows non-portable. | Use the package `fonts/` directory (or a documented configurable font root) as the default; retain explicit user paths as an override. | **Documented — owner action** |
| Low | `nodes/llm_bridge.py:48-56` | Provider/model/API key are supplied by the upstream toolkit context, not environment variables. Missing/placeholder credentials are rejected, but deployment configuration is implicit and undocumented in this package. | Document that `comfyui-llm-toolkit` provider configuration is required and that credentials must be entered through its credential mechanism; never commit keys. | **Documented — owner action** |
| Low | `nodes/llm_bridge.py:6`, several nodes | Diagnostic/error logs include exception text and truncated model responses. These may contain manuscript/IP data and should be treated as sensitive local logs; no API key is intentionally logged. | Avoid logging raw model responses in production, or provide a redacted/debug logging switch. | **Documented — owner action** |
| Low | `.github/workflows/publish.yml:11-27` | Publish workflow grants `issues: write` although publishing only needs repository checkout and the registry action's token. Excess permission increases CI blast radius. The workflow also has no build/import/security gate before publishing. | Set `permissions: contents: read` (and only the action-required permission), add compile/import/secret checks before publish, and pin third-party actions to reviewed SHAs. | **Documented — owner action** |
| Informational | `README.md`, `pyproject.toml` | README says to install `requirements.txt`, but no tracked requirements file exists; the manifest also omits runtime dependencies. This is primarily a reproducibility/functionality issue, not an authentication flaw. | Add a dependency declaration or accurate installation instructions, including the ComfyUI/LLM toolkit integration requirement. | **Documented — owner action** |

## Checks performed

- Secret patterns and credential-like literals were searched in the current tree and across reachable git history. No API keys, passwords, bearer tokens, cloud access keys, or connection strings were found. Workflow uses `${{ secrets.REGISTRY_ACCESS_TOKEN }}`; this is a GitHub secret reference, not a checked-in secret.
- No `.env` files, environment-variable readers, auth middleware, protected routes, CORS settings, JWT handling, SQL, `eval`, `exec`, `pickle`, unsafe YAML loading, or shell execution were found.
- LLM credentials are passed in-memory from `context["provider_config"]` by the external `comfyui-llm-toolkit`; this repository does not persist them.
- User text is interpolated into LLM prompts and Pillow drawing operations. There is no HTML/browser output or template engine in this package, so no direct XSS sink was identified.
- The font downloader now constrains both outbound font requests to Google Fonts hosts and response size/time. It still depends on TLS/certificate validation supplied by `requests`.

## Required environment/configuration variables

There are no environment variables read directly by this repository.

The following values are required in the upstream `comfyui-llm-toolkit` provider node/context when using LLM nodes; they are configuration fields, not environment variables read here:

| Name | Description |
|---|---|
| `provider_config.provider_name` | LLM provider identifier, e.g. OpenRouter or a local provider. |
| `provider_config.llm_model` | Provider model identifier. |
| `provider_config.api_key` | Provider credential supplied by the toolkit; keep secret and do not put it in workflow JSON committed to git. |
| `provider_config.base_ip` | Local/provider host when applicable; defaults to `localhost` in the bridge. |
| `provider_config.port` | Local/provider port when applicable; defaults to `11434` in the bridge. |

## Owner actions before release

1. Replace absolute OS-specific font defaults with package-relative defaults and document explicit font-path overrides.
2. Tighten GitHub Actions permissions, pin action revisions, and add compile/import/secret checks before registry publication.
3. Document the external toolkit credential setup and ensure exported workflow JSON never contains populated API-key widgets.
4. Decide whether manuscript/model-response logging is acceptable for the deployment threat model; otherwise redact or disable raw response logging.
5. Declare runtime dependencies and add a minimal smoke-test suite; the audit baseline collected zero tests.

## Audit conclusion

No checked-in secrets or HTTP authentication surfaces were found. The one directly remediable security issue was the unrestricted remote font URL/request behavior; it is fixed in code. Remaining findings are portability, CI hardening, dependency documentation, and local sensitive-log hygiene requiring owner decisions or release-process changes.
