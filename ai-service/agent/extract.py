import os

import boto3
from pydantic import BaseModel, model_validator

PROMPT = """Extract the text from this photo of a document.
Respond with JSON only, no markdown:
{"readable": true, "content": "<only the text visible in the image>"}
or
{"readable": false, "content": ""}
Set readable to false when the photo is blurry, cropped, or not a readable document.
Do not guess text you cannot see."""


class ImageExtraction(BaseModel):
    readable: bool
    content: str = ""

    @model_validator(mode="after")
    def clear_content_when_unreadable(self):
        if not self.readable:
            self.content = ""
        return self


def extract_image(image_bytes: bytes, media_type: str) -> ImageExtraction:
    response = boto3.client("bedrock-runtime").converse(
        modelId=os.environ["BEDROCK_MODEL_ID"],
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": PROMPT},
                    {
                        "image": {
                            "format": media_type,
                            "source": {"bytes": image_bytes},
                        }
                    },
                ],
            }
        ],
    )
    text = response["output"]["message"]["content"][0]["text"]
    return ImageExtraction.model_validate_json(text)
