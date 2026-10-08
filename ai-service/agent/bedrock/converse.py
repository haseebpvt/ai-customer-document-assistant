import boto3


def converse(model_id: str, content: list) -> str:
    response = boto3.client("bedrock-runtime").converse(
        modelId=model_id,
        messages=[{"role": "user", "content": content}],
    )
    return response["output"]["message"]["content"][0]["text"]
