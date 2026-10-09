import boto3


def converse(model_id: str, content: list) -> str:
    response = boto3.client("bedrock-runtime").converse(
        modelId=model_id,
        messages=[{"role": "user", "content": content}],
        inferenceConfig={"temperature": 0},
    )
    return response["output"]["message"]["content"][0]["text"]


def json_object(reply: str) -> str:
    # Models sometimes wrap the JSON in a markdown fence or add a sentence before it.
    return reply[reply.find("{") : reply.rfind("}") + 1]
