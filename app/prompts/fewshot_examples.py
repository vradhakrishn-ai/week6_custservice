def get_fewshot_examples() -> list[dict]:
    return [
        {"input": "What is the fee for NEFT?", "output": "The fee depends on the transfer amount and account type."},
        {"input": "I want to dispute a charge", "output": "I can help you start a dispute workflow."},
    ]
