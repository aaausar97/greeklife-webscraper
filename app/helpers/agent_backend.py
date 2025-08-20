import logging
from typing import List, Optional

import requests


class AgentBackendClient:
    """Minimal client for logging in and sending lead batches to the agent backend."""

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        login_path: Optional[str] = "/login",
        chunk_size: int = 300,
        timeout_seconds: int = 20,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.login_path = login_path or "/login"
        self.chunk_size = chunk_size
        self.timeout_seconds = timeout_seconds
        self._token = token

    def _login_get_token(self) -> Optional[str]:
        if not self.username or not self.password:
            return None

        login_url = f"{self.base_url}/{self.login_path.lstrip('/')}"

        # Try JSON body first (common for /login returning access_token)
        try:
            json_payload = {"username": self.username, "password": self.password}
            resp = requests.post(login_url, json=json_payload, timeout=self.timeout_seconds)
            if resp.ok:
                data = resp.json()
                token = data.get("access_token") or data.get("token")
                if token:
                    return token
        except Exception as e:
            logging.error(f"backend login (json) failed: {e}")

        # Fallback to form-encoded (common for /token password flow)
        try:
            form_payload = {
                "username": self.username,
                "password": self.password,
                "grant_type": "password",
            }
            resp = requests.post(login_url, data=form_payload, timeout=self.timeout_seconds)
            if resp.ok:
                data = resp.json()
                token = data.get("access_token") or data.get("token")
                if token:
                    return token
            else:
                logging.error(f"backend login failed: {resp.status_code} {resp.text}")
        except Exception as e:
            logging.error(f"backend login (form) failed: {e}")

        return None

    def _ensure_token(self) -> Optional[str]:
        if self._token:
            return self._token
        self._token = self._login_get_token()
        return self._token

    @staticmethod
    def _rows_to_dicts(rows_to_append: List[List[Optional[str]]]) -> List[dict]:
        keys = [
            "date",
            "username",
            "chapter_name",
            "phone_numbers",
            "emails",
            "tagged",
            "caption",
            "image_txt",
            "post_url",
            "post_image_url",
            "notes",
            "raw_content",
        ]
        dict_rows: List[dict] = []
        for row in rows_to_append:
            padded_row = [str(item) if item is not None else None for item in row] + [None] * (len(keys) - len(row))
            dict_rows.append(dict(zip(keys, padded_row)))
        return dict_rows

    def ingest(self, rows_to_append: List[List[Optional[str]]]) -> List[dict]:
        if not rows_to_append:
            return [{"status": "skipped", "reason": "no rows"}]

        token = self._ensure_token()
        if not token:
            logging.error("No token available for backend ingest")
            return [{"error": "token_unavailable"}]

        headers = {"Authorization": f"Bearer {token}"}

        dict_rows = self._rows_to_dicts(rows_to_append)
        results: List[dict] = []

        for i in range(0, len(dict_rows), self.chunk_size):
            chunk = dict_rows[i : i + self.chunk_size]
            try:
                response = requests.post(
                    f"{self.base_url}/leads/ingest",
                    json=chunk,
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                try:
                    results.append(response.json())
                except Exception:
                    results.append({"status_code": response.status_code, "text": response.text})
            except Exception as e:
                body_preview = chunk[:1]
                logging.error(f"backend ingest failed: {e}")
                if hasattr(e, "response") and e.response is not None:
                    try:
                        www = e.response.headers.get("WWW-Authenticate")
                    except Exception:
                        www = None
                    logging.error(
                        f"status: {e.response.status_code}, resp: {e.response.text}, www-authenticate: {www}"
                    )
                logging.error(
                    f"url: {self.base_url}, payload_count: {len(chunk)}, first_row: {body_preview}"
                )
                results.append({"error": str(e)})

        return results


