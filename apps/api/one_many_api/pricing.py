"""Deterministic price allocation; no floats and no unapproved financial charges."""


def equal_shares(price_minor: int, participants: int) -> list[int]:
    if not isinstance(price_minor, int) or isinstance(price_minor, bool) or price_minor <= 0:
        raise ValueError("Price must be a positive integer in minor units")
    if not isinstance(participants, int) or isinstance(participants, bool) or participants < 2:
        raise ValueError("At least two prospective participants are required")
    if participants > price_minor:
        raise ValueError("Each participant must receive a positive allocation")
    quotient, remainder = divmod(price_minor, participants)
    # First N hypothetical shares receive one extra minor unit; total is exact.
    shares = [quotient + (i < remainder) for i in range(participants)]
    assert sum(shares) == price_minor
    return shares


def hypothetical_savings(price_minor: int, participants: int) -> int:
    """Upper bound if each person would have purchased the same item separately."""
    return price_minor * (participants - 1)
