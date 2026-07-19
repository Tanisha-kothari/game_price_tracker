import base64
import json
import logging
from typing import Optional

import requests

from utils import dump_json_to_string

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"


class GitHubManager:
    def __init__(self, token: str, owner: str, repo: str):
        self.token = token
        self.owner = owner
        self.repo = repo
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "GamePriceTracker/1.0",
        }
        self._base_url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"

    def _request(self, method: str, endpoint: str = "", **kwargs) -> requests.Response:
        if endpoint:
            url = f"{self._base_url}/{endpoint.lstrip('/')}"
        else:
            url = self._base_url

        return requests.request(
        method,
        url,
        headers=self._headers,
        timeout=20,
        **kwargs,
    )

    def get_file_content(self, path: str) -> Optional[str]:
        try:
            resp = self._request("GET", f"contents/{path}")
            if resp.status_code == 404:
                logger.info("File %s not found in repo, returning None", path)
                return None
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", "")
            if content:
                decoded = base64.b64decode(content).decode("utf-8")
                return decoded
            return ""
        except requests.RequestException as e:
            logger.error("Failed to fetch %s from GitHub: %s", path, e)
            raise

    def get_file_sha(self, path: str) -> Optional[str]:
        try:
            resp = self._request("GET", f"contents/{path}")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            return data.get("sha")
        except requests.RequestException:
            return None

    def create_file(self, path: str, content: str, message: str) -> dict:
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": message,
            "content": encoded,
        }
        resp = self._request("PUT", f"contents/{path}", json=payload)
        if resp.status_code not in (201, 200):
            logger.error("GitHub create file failed: %d %s", resp.status_code, resp.text)
            resp.raise_for_status()
        logger.info("GitHub file created: %s", path)
        return resp.json()

    def update_file(self, path: str, content: str, message: str, sha: str) -> dict:
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": message,
            "content": encoded,
            "sha": sha,
        }
        resp = self._request("PUT", f"contents/{path}", json=payload)
        if resp.status_code not in (200, 201):
            logger.error("GitHub update file failed: %d %s", resp.status_code, resp.text)
            resp.raise_for_status()
        logger.info("GitHub file updated: %s", path)
        return resp.json()

    def save_file(self, path: str, content: str, message: str) -> dict:
        sha = self.get_file_sha(path)
        if sha:
            return self.update_file(path, content, message, sha)
        return self.create_file(path, content, message)

    def read_games(self) -> tuple[list[dict], bool]:
        content = self.get_file_content("games.json")
        if content is None:
            return [], False
        return json.loads(content), True

    def save_games(self, games: list[dict], message: str = "Update games.json") -> dict:
        content = dump_json_to_string(games)
        return self.save_file("games.json", content, message)

    def read_history(self) -> dict[str, dict[str, float]]:
        content = self.get_file_content("history.json")
        if content is None:
            return {}
        return json.loads(content)

    def save_history(self, history: dict, message: str = "Update history.json") -> dict:
        content = dump_json_to_string(history)
        return self.save_file("history.json", content, message)

    def test_connection(self) -> bool:
        try:
            print("=" * 60)
            print("URL:", self._base_url)
            print("Headers:", self._headers)

            resp = requests.get(
            self._base_url,
            headers=self._headers,
            timeout=20,
            )

            print("Status:", resp.status_code)
            print("Response:", resp.text)
            print("=" * 60)

            resp.raise_for_status()
            return True

        except Exception as e:
            print("ERROR:", e)
            return False
