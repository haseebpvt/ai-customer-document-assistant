import json
import logging
import os

import boto3

from agent.graph import graph
from agent.progress import update_document

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worker")

# Same number as maxReceiveCount on the queue in terraform/storage.tf.
MAX_RECEIVES = 3
RETRY_DELAY_SECONDS = 30


def run():
    sqs = boto3.client("sqs")
    queue_url = os.environ["SQS_QUEUE_URL"]
    while True:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            MessageSystemAttributeNames=["ApproximateReceiveCount"],
        )
        messages = response.get("Messages", [])
        if not messages:
            continue
        message = messages[0]
        receives = int(message.get("Attributes", {}).get("ApproximateReceiveCount", 1))
        try:
            body = json.loads(message["Body"])
            document_id = body["document_id"]
            s3_key = body["s3_key"]
        except (ValueError, KeyError, TypeError):
            # No document id to report against. SQS moves it to the dead-letter queue.
            log.exception("unreadable queue message %s", message.get("MessageId"))
            continue
        log.info("document %s started, receive %s", document_id, receives)
        try:
            # content_type stays on the message. The graph uses the file extension.
            graph.invoke({"document_id": document_id, "s3_key": s3_key})
        except Exception as error:
            log.exception("document %s failed on receive %s", document_id, receives)
            last = receives >= MAX_RECEIVES
            # The UI keeps polling on retrying. failed is final.
            update_document(
                document_id,
                status="failed" if last else "retrying",
                error_message=str(error),
            )
            if not last:
                sqs.change_message_visibility(
                    QueueUrl=queue_url,
                    ReceiptHandle=message["ReceiptHandle"],
                    VisibilityTimeout=RETRY_DELAY_SECONDS,
                )
            continue
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )
        log.info("document %s finished", document_id)


if __name__ == "__main__":
    run()
