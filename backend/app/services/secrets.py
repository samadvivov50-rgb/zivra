from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import Settings


class SecretStoreUnavailableError(RuntimeError):
    """Raised when encrypted secret storage is not available."""


class BaseSecretProtector:
    provider = "unavailable"
    label = "Encrypted vault unavailable"
    available = False

    def protect(self, plaintext: str) -> str:
        raise SecretStoreUnavailableError("Encrypted secret storage is not available on this platform.")

    def unprotect(self, ciphertext: str) -> str:
        raise SecretStoreUnavailableError("Encrypted secret storage is not available on this platform.")


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class _DataBlob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


    class WindowsDpapiProtector(BaseSecretProtector):
        provider = "windows_dpapi"
        label = "Windows Data Protection API"
        available = True
        _ENTROPY = b"zivra-local-vault"

        def __init__(self) -> None:
            self._crypt32 = ctypes.windll.crypt32
            self._kernel32 = ctypes.windll.kernel32
            self._crypt32.CryptProtectData.argtypes = [
                ctypes.POINTER(_DataBlob),
                wintypes.LPCWSTR,
                ctypes.POINTER(_DataBlob),
                ctypes.c_void_p,
                ctypes.c_void_p,
                wintypes.DWORD,
                ctypes.POINTER(_DataBlob),
            ]
            self._crypt32.CryptProtectData.restype = wintypes.BOOL
            self._crypt32.CryptUnprotectData.argtypes = [
                ctypes.POINTER(_DataBlob),
                ctypes.POINTER(wintypes.LPWSTR),
                ctypes.POINTER(_DataBlob),
                ctypes.c_void_p,
                ctypes.c_void_p,
                wintypes.DWORD,
                ctypes.POINTER(_DataBlob),
            ]
            self._crypt32.CryptUnprotectData.restype = wintypes.BOOL
            self._kernel32.LocalFree.argtypes = [ctypes.c_void_p]
            self._kernel32.LocalFree.restype = ctypes.c_void_p

        def protect(self, plaintext: str) -> str:
            encrypted = self._protect_bytes(str(plaintext or "").encode("utf-8"))
            return base64.b64encode(encrypted).decode("ascii")

        def unprotect(self, ciphertext: str) -> str:
            raw = base64.b64decode(str(ciphertext or "").encode("ascii"))
            decrypted = self._unprotect_bytes(raw)
            return decrypted.decode("utf-8")

        def _protect_bytes(self, payload: bytes) -> bytes:
            input_blob, input_buffer = self._blob_from_bytes(payload)
            entropy_blob, entropy_buffer = self._blob_from_bytes(self._ENTROPY)
            del input_buffer, entropy_buffer
            output_blob = _DataBlob()
            if not self._crypt32.CryptProtectData(
                ctypes.byref(input_blob),
                "Zivra secret",
                ctypes.byref(entropy_blob),
                None,
                None,
                0,
                ctypes.byref(output_blob),
            ):
                raise SecretStoreUnavailableError("Windows encrypted storage failed while protecting a secret.")
            try:
                return ctypes.string_at(output_blob.pbData, output_blob.cbData)
            finally:
                self._kernel32.LocalFree(output_blob.pbData)

        def _unprotect_bytes(self, payload: bytes) -> bytes:
            input_blob, input_buffer = self._blob_from_bytes(payload)
            entropy_blob, entropy_buffer = self._blob_from_bytes(self._ENTROPY)
            del input_buffer, entropy_buffer
            output_blob = _DataBlob()
            description = wintypes.LPWSTR()
            if not self._crypt32.CryptUnprotectData(
                ctypes.byref(input_blob),
                ctypes.byref(description),
                ctypes.byref(entropy_blob),
                None,
                None,
                0,
                ctypes.byref(output_blob),
            ):
                raise SecretStoreUnavailableError("Windows encrypted storage failed while unlocking a secret.")
            try:
                return ctypes.string_at(output_blob.pbData, output_blob.cbData)
            finally:
                self._kernel32.LocalFree(output_blob.pbData)
                if description:
                    self._kernel32.LocalFree(description)

        def _blob_from_bytes(self, payload: bytes) -> tuple[_DataBlob, ctypes.Array[ctypes.c_char]]:
            buffer = ctypes.create_string_buffer(payload)
            return _DataBlob(len(payload), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


else:
    class WindowsDpapiProtector(BaseSecretProtector):
        pass


def build_default_secret_protector() -> BaseSecretProtector:
    protector = WindowsDpapiProtector()
    return protector if getattr(protector, "available", False) else BaseSecretProtector()


@dataclass(frozen=True, slots=True)
class SecretField:
    key: str
    label: str
    masked_kind: str


class SecretsService:
    SECRET_FIELDS: tuple[SecretField, ...] = (
        SecretField("llm_api_key", "LLM API key", "token"),
        SecretField("smtp_username", "SMTP username", "username"),
        SecretField("smtp_password", "SMTP password", "password"),
        SecretField("whatsapp_access_token", "WhatsApp access token", "token"),
        SecretField("whatsapp_app_secret", "WhatsApp app secret", "password"),
    )

    def __init__(self, path: Path, *, protector: BaseSecretProtector | None = None) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.protector = protector or build_default_secret_protector()

    def apply_to_settings(self, settings: Settings) -> dict[str, str]:
        settings.refresh_integration_settings_from_environment()
        stored = self.load_values()
        for field in self.SECRET_FIELDS:
            value = stored.get(field.key, "").strip()
            if value:
                setattr(settings, field.key, value)
        if not os.getenv("ZIVRA_EMAIL_FROM", "").strip():
            settings.email_from_address = settings.smtp_username.strip()
        return stored

    def snapshot(self, settings: Settings) -> dict[str, Any]:
        stored = self.load_values()
        fields: dict[str, Any] = {}
        for field in self.SECRET_FIELDS:
            stored_value = stored.get(field.key, "").strip()
            env_value = self._env_value(field.key)
            active_value = stored_value or env_value
            source = "vault" if stored_value else "environment" if env_value else "unset"
            fields[field.key] = {
                "label": field.label,
                "configured": bool(active_value),
                "source": source,
                "stored_in_vault": bool(stored_value),
                "masked_value": self._mask_value(active_value, kind=field.masked_kind),
            }

        planner_ready = bool(settings.llm_model.strip() and settings.llm_api_key.strip() and settings.planner_mode != "rule")
        smtp_ready = bool(settings.smtp_host.strip() and (settings.email_from_address.strip() or settings.smtp_username.strip()))
        whatsapp_ready = bool(settings.whatsapp_phone_number_id.strip() and settings.whatsapp_access_token.strip())
        return {
            "provider": {
                "available": bool(self.protector.available),
                "provider": self.protector.provider,
                "label": self.protector.label,
            },
            "fields": fields,
            "runtime": {
                "planner_mode": settings.planner_mode,
                "planner_model": settings.llm_model,
                "planner_ready": planner_ready,
                "smtp_host": settings.smtp_host,
                "smtp_port": settings.smtp_port,
                "smtp_ready": smtp_ready,
                "whatsapp_api_version": settings.whatsapp_api_version,
                "whatsapp_phone_number_id": settings.whatsapp_phone_number_id,
                "whatsapp_ready": whatsapp_ready,
                "whatsapp_verify_token_configured": bool(settings.whatsapp_verify_token.strip()),
                "whatsapp_signature_ready": bool(settings.whatsapp_app_secret.strip()),
            },
        }

    def update(self, settings: Settings, updates: dict[str, Any]) -> dict[str, Any]:
        if not self.protector.available:
            raise SecretStoreUnavailableError("Encrypted secret storage is not available on this platform.")

        current = self._load_raw_payload()
        secrets = dict(current.get("secrets", {}))
        changed = False

        for field in self.SECRET_FIELDS:
            if field.key not in updates:
                continue
            value = str(updates.get(field.key, "") or "").strip()
            if value:
                secrets[field.key] = self.protector.protect(value)
            else:
                secrets.pop(field.key, None)
            changed = True

        if not changed:
            self.apply_to_settings(settings)
            return self.snapshot(settings)

        payload = {
            "version": 1,
            "provider": self.protector.provider,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "secrets": secrets,
        }
        self._write_raw_payload(payload)
        self.apply_to_settings(settings)
        return self.snapshot(settings)

    def clear(self, settings: Settings, *, keys: list[str] | None = None) -> dict[str, Any]:
        current = self._load_raw_payload()
        secrets = dict(current.get("secrets", {}))
        target_keys = set(keys or [field.key for field in self.SECRET_FIELDS])
        for key in target_keys:
            secrets.pop(key, None)

        if secrets:
            payload = {
                "version": 1,
                "provider": current.get("provider", self.protector.provider),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "secrets": secrets,
            }
            self._write_raw_payload(payload)
        elif self.path.exists():
            self.path.unlink()

        self.apply_to_settings(settings)
        return self.snapshot(settings)

    def load_values(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        if not self.protector.available:
            return {}

        raw = self._load_raw_payload()
        decrypted: dict[str, str] = {}
        for field in self.SECRET_FIELDS:
            encrypted = str(raw.get("secrets", {}).get(field.key, "") or "").strip()
            if not encrypted:
                continue
            try:
                decrypted[field.key] = self.protector.unprotect(encrypted).strip()
            except Exception:
                continue
        return decrypted

    def _load_raw_payload(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "provider": self.protector.provider, "secrets": {}}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"version": 1, "provider": self.protector.provider, "secrets": {}}
        if not isinstance(payload, dict):
            return {"version": 1, "provider": self.protector.provider, "secrets": {}}
        if not isinstance(payload.get("secrets"), dict):
            payload["secrets"] = {}
        return payload

    def _write_raw_payload(self, payload: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _env_value(self, key: str) -> str:
        if key == "llm_api_key":
            return os.getenv("ZIVRA_LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")).strip()
        if key == "smtp_username":
            return os.getenv("ZIVRA_SMTP_USERNAME", "").strip()
        if key == "smtp_password":
            return os.getenv("ZIVRA_SMTP_PASSWORD", "").strip()
        if key == "whatsapp_access_token":
            return os.getenv("ZIVRA_WHATSAPP_ACCESS_TOKEN", "").strip()
        if key == "whatsapp_app_secret":
            return os.getenv("ZIVRA_WHATSAPP_APP_SECRET", "").strip()
        return ""

    def _mask_value(self, value: str, *, kind: str) -> str:
        cleaned = str(value or "").strip()
        if not cleaned:
            return ""
        if kind == "password":
            return "stored"
        if kind == "token":
            if len(cleaned) <= 6:
                return "*" * len(cleaned)
            return f"{cleaned[:4]}...{cleaned[-2:]}"
        if kind == "username" and "@" in cleaned:
            local, domain = cleaned.split("@", 1)
            local_mask = f"{local[:2]}..." if local else "..."
            return f"{local_mask}@{domain}"
        if len(cleaned) <= 4:
            return cleaned[0] + "***"
        return f"{cleaned[:3]}..."
