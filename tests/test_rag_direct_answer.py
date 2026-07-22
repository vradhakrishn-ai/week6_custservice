import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.model import RetrievedChunk
from app.rag_pipeline import should_use_direct_answer


def test_neft_charge_query_uses_direct_answer_for_lexical_match():
    contexts = [
        RetrievedChunk(
            content="NEFT for transactions Up to Rs. 10,000: Rs. 2 + GST (Online banking)",
            source="upi_neft_charges.csv",
            score=0.12,
        )
    ]

    assert should_use_direct_answer(
        "What are the charges for NEFT Up to Rs. 10,000?",
        contexts,
    ) is True


def test_non_direct_factual_query_does_not_use_direct_answer():
    contexts = [
        RetrievedChunk(
            content="The latest trends in global banking include AI-assisted advisory and open banking.",
            source="general.txt",
            score=0.12,
        )
    ]

    assert should_use_direct_answer(
        "What are the latest trends in global banking?",
        contexts,
    ) is False
