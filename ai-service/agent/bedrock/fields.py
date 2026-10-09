import json
import os

from pydantic import BaseModel, ConfigDict

from agent.bedrock.classify import DocumentType
from agent.bedrock.converse import converse, json_object


class Fields(BaseModel):
    # A model may return 1250.5 instead of "1250.5". Keep every value a string.
    model_config = ConfigDict(coerce_numbers_to_str=True)


class IdentityDocument(Fields):
    customer_name: str | None = None
    id_number: str | None = None
    expiry_date: str | None = None
    date_of_birth: str | None = None


class ClaimForm(Fields):
    customer_name: str | None = None
    claim_reference: str | None = None
    date: str | None = None
    amount: str | None = None


class PolicyDocument(Fields):
    customer_name: str | None = None
    policy_number: str | None = None
    effective_date: str | None = None


class CustomerCorrespondence(Fields):
    customer_name: str | None = None
    date: str | None = None


class SupportingEvidence(Fields):
    date: str | None = None
    description: str | None = None


SCHEMAS: dict[DocumentType, type[BaseModel]] = {
    "Identity Document": IdentityDocument,
    "Claim Form": ClaimForm,
    "Policy Document": PolicyDocument,
    "Customer Correspondence": CustomerCorrespondence,
    "Supporting Evidence": SupportingEvidence,
}


def extract_fields(text: str, document_type: DocumentType) -> BaseModel:
    model = SCHEMAS[document_type]
    prompt = (
        "Extract the fields for this document.\n"
        "Use null when a value is not visible. Do not guess.\n"
        "For customer_name on correspondence, use the customer or the sender.\n"
        "Respond with JSON only, no markdown.\n"
        "Schema:\n"
        + json.dumps(model.model_json_schema())
    )
    reply = converse(
        os.environ["BEDROCK_CLASSIFY_MODEL_ID"],
        [{"text": prompt}, {"text": text}],
    )
    return model.model_validate_json(json_object(reply))
