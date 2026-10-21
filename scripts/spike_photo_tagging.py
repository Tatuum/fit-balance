"""Spike: ask an LLM which styling techniques a garment photo shows.

Offline utility (docs/plans/0012, Spike 1). Not imported by the app; needs
ANTHROPIC_API_KEY and the `spike` dependency group. Never run in CI.

    uv run --env-file .env --group spike python scripts/spike_photo_tagging.py photo.jpg
"""

import base64
import sys
from pathlib import Path

from pydantic import BaseModel

from fit_balance.scoring import load_effects_table

MODEL = "claude-sonnet-5-5"
_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


class SpikeResult(BaseModel):
    techniques: list[str]
    uncertain_note: str | None = None


def build_prompt(vocabulary: list[str]) -> str:
    schema = SpikeResult.model_json_schema()
    return (
        "You are looking at a photo of a single garment. Decide which of the following "
        "styling techniques the garment has. Use only names from this list, exactly as "
        "written:\n\n"
        + "\n".join(f"- {name}" for name in vocabulary)
        + "\n\nIf the garment has a notable feature that none of these cover, or you are "
        "unsure about a technique, do not invent a name; describe it briefly in "
        "`uncertain_note`.\n\n"
        "Reply with JSON only, matching this schema:\n"
        f"{schema}"
    )


def parse_response(raw: str) -> SpikeResult:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    return SpikeResult.model_validate_json(text)


def tag_photo(image_path: Path) -> SpikeResult:
    import anthropic

    media_type = _MEDIA_TYPES.get(image_path.suffix.lower())
    if media_type is None:
        raise ValueError(f"unsupported image type: {image_path.suffix}")
    data = base64.standard_b64encode(image_path.read_bytes()).decode()
    prompt = build_prompt(list(load_effects_table()))

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": data},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return parse_response(message.content[0].text)


def main(paths: list[str]) -> None:
    for path in paths:
        result = tag_photo(Path(path))
        print(f"{path}")
        print(f"  techniques: {', '.join(result.techniques) or '(none)'}")
        if result.uncertain_note:
            print(f"  uncertain:  {result.uncertain_note}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: spike_photo_tagging.py <photo> [<photo> ...]")
    main(sys.argv[1:])
