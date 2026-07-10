import sys
import os
import folder_paths

# Diagnostic: confirm which bridge file ComfyUI actually loaded (catches stale copies).
print(f"[MiniBook] bridge loaded from {__file__}")

# Ensure comfyui-llm-toolkit is on sys.path so we can import its internals.
llm_toolkit_path = os.path.join(folder_paths.get_folder_paths("custom_nodes")[0], "comfyui-llm-toolkit")
if llm_toolkit_path not in sys.path:
    sys.path.append(llm_toolkit_path)

try:
    from send_request import send_request, run_async
    _toolkit_available = True
except ImportError:
    send_request = None
    run_async = None
    _toolkit_available = False
    print("[MiniBook] Warning: comfyui-llm-toolkit not found or send_request import failed.")


def run_llm(context, system_prompt, user_prompt, max_tokens=2048, temperature=0.7):
    """
    Bridge to call the LLM Toolkit's send_request function synchronously.

    The toolkit's ``APIProviderSelectorNode`` packages provider/model/key under
    ``context["provider_config"]`` using the keys ``provider_name``, ``llm_model``,
    ``api_key``, ``base_ip`` and ``port``. This bridge unwraps them and calls
    ``send_request`` with its real argument names so calls actually reach the
    intended provider with valid credentials.

    ``max_tokens`` and ``temperature`` are exposed as kwargs so callers that
    need a large structured response (e.g. the Literary Editor emitting a
    multi-page JSON plan) can request enough headroom to avoid mid-response
    truncation. The toolkit's send_request default is only 2048 tokens.

    Raises on any failure so that callers treat their local fallbacks as the
    last resort, not the normal path.
    """
    if not _toolkit_available:
        raise RuntimeError("comfyui-llm-toolkit is missing. Cannot call LLM.")

    cfg = {}
    if isinstance(context, dict):
        cfg = context.get("provider_config") or {}

    provider = cfg.get("provider_name", "openrouter")
    model = cfg.get("llm_model", "google/gemini-2.5-flash")
    api_key = cfg.get("api_key", "")

    # The provider node substitutes "1234" when it cannot resolve a real key.
    # Treat that the same as a missing key so we fail loudly instead of sending
    # an invalid key upstream.
    if not api_key or api_key == "1234":
        raise RuntimeError(f"[llm_bridge] No usable API key resolved for {provider}.")

    result = run_async(send_request(
        llm_provider=provider,
        base_ip=cfg.get("base_ip") or "localhost",
        port=cfg.get("port") or "11434",
        llm_model=model,
        system_message=system_prompt,
        user_message=user_prompt,
        llm_api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
    ))

    # ``send_request`` may return None, an error dict, or an OpenAI-style response.
    if result is None:
        raise RuntimeError("[llm_bridge] send_request returned None (see console for the underlying error).")

    if isinstance(result, dict):
        if "error" in result:
            err = result["error"]
            err_msg = err if isinstance(err, str) else repr(err)
            raise RuntimeError(f"[llm_bridge] send_request returned an error: {err_msg}")

        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise RuntimeError(f"Unexpected LLM response format from toolkit: {result} - {e}")

    # Non-dict result is unexpected here; surface it for diagnosis.
    raise RuntimeError(f"[llm_bridge] send_request returned an unexpected type ({type(result).__name__}): {result!r}")
