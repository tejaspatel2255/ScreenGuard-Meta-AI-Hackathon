from scripts.check_claims import check_claims


def test_claims_audit() -> None:
    """Verifies that documentation and frontend code do not make false claims."""
    assert check_claims() == 0
