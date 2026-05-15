"""
LLM-based content classifier for EVALUATION (copied from version3).
"""

import requests
import time
from typing import Literal
from theme.constants import (
    OLLAMA_BASE,
    API_KEY,
    DEFAULT_MODEL,
    CLASSIFICATION_PROMPT,
    STATUS_ICONS,
)

SensitivityLevel = Literal["public", "internal", "confidential"]

class ContentClassifier:
    def __init__(
        self,
        ollama_base: str = OLLAMA_BASE,
        model: str = DEFAULT_MODEL,
        api_key: str = API_KEY,
    ):
        self.ollama_base = ollama_base
        self.model = model
        self.headers = {"x-api-key": api_key}
        self.stats = {"total": 0, "public": 0, "internal": 0, "confidential": 0, "errors": 0}

    def classify_chunk(self, text: str, max_retries: int = 3, timeout: int = 30) -> SensitivityLevel:
        text_for_classification = text[:2000] if len(text) > 2000 else text
        prompt = CLASSIFICATION_PROMPT.format(text=text_for_classification)

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.ollama_base}/llm",
                    json={"model": self.model, "prompt": prompt},
                    headers=self.headers,
                    timeout=timeout,
                )

                if response.status_code != 200:
                    raise Exception(f"API returned status {response.status_code}")

                result = response.json()["response"].strip().upper()

                if "PUBLIC" in result:
                    level = "public"
                elif "INTERNAL" in result:
                    level = "internal"
                elif "CONFIDENTIAL" in result:
                    level = "confidential"
                else:
                    print(f"{STATUS_ICONS['warning']} Unclear classification: '{result}', defaulting to INTERNAL")
                    level = "internal"

                self.stats["total"] += 1
                self.stats[level] += 1

                return level

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"{STATUS_ICONS['warning']} Timeout, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"{STATUS_ICONS['error']} Classification timeout, defaulting to INTERNAL")
                    self.stats["errors"] += 1
                    return "internal"

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"{STATUS_ICONS['warning']} Error: {e}, retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(2)
                else:
                    print(f"{STATUS_ICONS['error']} Classification failed: {e}, defaulting to INTERNAL")
                    self.stats["errors"] += 1
                    return "internal"

        return "internal"

    def classify_batch(self, texts: list[str], show_progress: bool = True) -> list[SensitivityLevel]:
        results = []
        total = len(texts)
        for i, text in enumerate(texts, 1):
            if show_progress and i % 5 == 0:
                print(f"{STATUS_ICONS['progress']} Classifying chunk {i}/{total}...")
            level = self.classify_chunk(text)
            results.append(level)
        return results

    def get_stats(self) -> dict:
        return self.stats.copy()

    def print_stats(self):
        print(f"\n{STATUS_ICONS['complete']} Classification Statistics:")
        print(f"  Total chunks: {self.stats['total']}")
        print(f"  🟢 PUBLIC: {self.stats['public']}")
        print(f"  🟡 INTERNAL: {self.stats['internal']}")
        print(f"  🔒 CONFIDENTIAL: {self.stats['confidential']}")
        if self.stats['errors'] > 0:
            print(f"  {STATUS_ICONS['error']} Errors: {self.stats['errors']}")


def classify_text(text: str) -> SensitivityLevel:
    classifier = ContentClassifier()
    return classifier.classify_chunk(text)
