"""Cognito custom email sender example using Loops transactional email.

AWS docs:
https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-custom-email-sender.html

Set these environment variables:
- LOOPS_API_KEY
- LOOPS_TXN_SIGNUP
- LOOPS_TXN_ADMIN_CREATE_USER
- LOOPS_TXN_RESEND_CODE
- LOOPS_TXN_FORGOT_PASSWORD
- LOOPS_TXN_UPDATE_USER_ATTRIBUTE
- LOOPS_TXN_VERIFY_USER_ATTRIBUTE
- LOOPS_TXN_AUTHENTICATION

Optional:
- LOOPS_USER_AGENT (default: "cognito-email-sender/1.0")
- COGNITO_CODE_IS_PLAINTEXT=1 for local/dev fallback
"""

from __future__ import annotations

import os
from typing import Any

from loops_py import LoopsClient, SendTransactionalEmailRequest

TRIGGER_TO_TXN_ENV: dict[str, str] = {
    "CustomEmailSender_SignUp": "LOOPS_TXN_SIGNUP",
    "CustomEmailSender_AdminCreateUser": "LOOPS_TXN_ADMIN_CREATE_USER",
    "CustomEmailSender_ResendCode": "LOOPS_TXN_RESEND_CODE",
    "CustomEmailSender_ForgotPassword": "LOOPS_TXN_FORGOT_PASSWORD",
    "CustomEmailSender_UpdateUserAttribute": "LOOPS_TXN_UPDATE_USER_ATTRIBUTE",
    "CustomEmailSender_VerifyUserAttribute": "LOOPS_TXN_VERIFY_USER_ATTRIBUTE",
    "CustomEmailSender_Authentication": "LOOPS_TXN_AUTHENTICATION",
}


def _get_client() -> LoopsClient:
    api_key = os.environ["LOOPS_API_KEY"]
    user_agent = os.getenv("LOOPS_USER_AGENT", "cognito-email-sender/1.0")
    return LoopsClient(api_key=api_key, user_agent=user_agent)


def _decrypt_cognito_code(event: dict[str, Any]) -> str:
    """Return a display-ready verification code.

    Cognito custom sender events typically provide an encrypted code in
    ``event['request']['code']``. In production, decrypt it using AWS KMS /
    AWS Encryption SDK according to AWS docs.

    For local development, set COGNITO_CODE_IS_PLAINTEXT=1 to use the code
    value directly.
    """
    raw_code = str(event.get("request", {}).get("code", "")).strip()
    if not raw_code:
        return ""

    if os.getenv("COGNITO_CODE_IS_PLAINTEXT") == "1":
        return raw_code

    raise NotImplementedError(
        "Decrypt event['request']['code'] per Cognito custom sender docs: "
        "https://docs.aws.amazon.com/cognito/latest/developerguide/"
        "user-pool-lambda-custom-email-sender.html"
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    trigger_source = str(event.get("triggerSource", ""))
    txn_env_var = TRIGGER_TO_TXN_ENV.get(trigger_source)

    if not txn_env_var:
        return event

    transactional_id = os.getenv(txn_env_var)
    if not transactional_id:
        return event

    email = str(event.get("request", {}).get("userAttributes", {}).get("email", "")).strip()
    if not email:
        return event

    code = _decrypt_cognito_code(event)

    username = str(event.get("userName", ""))
    request_id = getattr(context, "aws_request_id", "no-request-id")
    idempotency_key = f"cognito:{trigger_source}:{username}:{request_id}"

    data_variables = {
        "code": code,
        "username": username,
        "trigger_source": trigger_source,
    }

    client = _get_client()
    client.transactional.send_transactional_email(
        SendTransactionalEmailRequest(
            transactional_id=transactional_id,
            email=email,
            data_variables=data_variables,
        ),
        idempotency_key=idempotency_key,
    )

    return event
