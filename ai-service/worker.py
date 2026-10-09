import json
import os

import boto3

from agent.graph import graph
from agent.progress import update_document


def run():
    sqs = boto3.client("sqs")
    queue_url = os.environ["SQS_QUEUE_URL"]
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
        )
        messages = response.get("Messages", [])
        if not messages:
            continue
        message = messages[0]
        body = json.loads(message["Body"])
        try:
            # content_type stays on the message. The graph uses the file extension.
            graph.invoke(
                {
                    "document_id": body["document_id"],
                    "s3_key": body["s3_key"],
                }
            )
        except Exception as error:
            # Leave the message so SQS can retry. A later success overwrites failed.
            update_document(
                body["document_id"],
                status="failed",
                error_message=str(error),
            )
            continue
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )


if __name__ == "__main__":
    run()
