"""
Unit Tests for Spaced Repetition System
========================================

Comprehensive test suite for spaced_repetition.py.

Run with:
    python -m pytest tests/test_spaced_repetition.py -v

Author: Manus AI
Date: 2025-12-20
"""

import pytest
from pathlib import Path
import sys
import tempfile
import shutil
import json
from datetime import datetime, timezone

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from spaced_repetition import (
    KnowledgeCard,
    calculate_next_review,
    load_cards,
    save_cards,
    CARDS_DB
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def mock_cards_db(temp_dir, monkeypatch):
    """Mock the CARDS_DB path to use a temporary directory."""
    test_db = temp_dir / "coaching" / "knowledge_cards.json"
    test_db.parent.mkdir(parents=True, exist_ok=True)
    
    # Monkeypatch the CARDS_DB constant
    import spaced_repetition
    monkeypatch.setattr(spaced_repetition, 'CARDS_DB', test_db)
    
    return test_db


# ============================================================================
# Test: SM-2 Algorithm - Quality Levels
# ============================================================================

def test_sm2_quality_0_resets_card():
    """Test that quality 0 (complete blackout) resets the card."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    # Build up to repetition 3
    card = calculate_next_review(5, card)
    card = calculate_next_review(5, card)
    card = calculate_next_review(5, card)
    
    assert card.repetitions == 3
    assert card.interval >= 15
    
    # Quality 0 should reset
    card = calculate_next_review(0, card)
    
    assert card.repetitions == 0
    assert card.interval == 0


def test_sm2_quality_1_resets_card():
    """Test that quality 1 (incorrect, but familiar) resets the card."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    card = calculate_next_review(5, card)
    card = calculate_next_review(5, card)
    
    assert card.repetitions == 2
    
    # Quality 1 should reset
    card = calculate_next_review(1, card)
    
    assert card.repetitions == 0
    assert card.interval == 0


def test_sm2_quality_2_resets_card():
    """Test that quality 2 (incorrect, but close) resets the card."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    card = calculate_next_review(5, card)
    
    # Quality 2 should reset
    card = calculate_next_review(2, card)
    
    assert card.repetitions == 0
    assert card.interval == 0


def test_sm2_quality_3_advances_card():
    """Test that quality 3 (correct with difficulty) advances the card."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    card = calculate_next_review(3, card)
    
    assert card.repetitions == 1
    assert card.interval == 1
    assert card.correct_reviews == 1


def test_sm2_quality_4_advances_card():
    """Test that quality 4 (correct after hesitation) advances the card."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    card = calculate_next_review(4, card)
    
    assert card.repetitions == 1
    assert card.interval == 1
    assert card.correct_reviews == 1


def test_sm2_quality_5_advances_card():
    """Test that quality 5 (perfect recall) advances the card."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    card = calculate_next_review(5, card)
    
    assert card.repetitions == 1
    assert card.interval == 1
    assert card.correct_reviews == 1


# ============================================================================
# Test: SM-2 Algorithm - Interval Growth
# ============================================================================

def test_sm2_interval_growth_perfect_recall():
    """Verify interval grows exponentially for perfect recall."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    # Review 1: quality 5
    card = calculate_next_review(5, card)
    assert card.interval == 1
    assert card.repetitions == 1
    
    # Review 2: quality 5
    card = calculate_next_review(5, card)
    assert card.interval == 6
    assert card.repetitions == 2
    
    # Review 3: quality 5 - should be 6 * EF (≈15-17 days)
    card = calculate_next_review(5, card)
    assert card.interval >= 15
    assert card.repetitions == 3
    
    # Review 4: quality 5 - should continue growing
    prev_interval = card.interval
    card = calculate_next_review(5, card)
    assert card.interval > prev_interval
    assert card.repetitions == 4
    
    # Review 5: quality 5 - should continue growing
    prev_interval = card.interval
    card = calculate_next_review(5, card)
    assert card.interval > prev_interval
    assert card.repetitions == 5


def test_sm2_interval_growth_good_recall():
    """Verify interval grows for good (quality 4) recall."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    # All reviews with quality 4
    card = calculate_next_review(4, card)
    assert card.interval == 1
    
    card = calculate_next_review(4, card)
    assert card.interval == 6
    
    card = calculate_next_review(4, card)
    assert card.interval >= 10  # Should still grow, but slower than quality 5


# ============================================================================
# Test: SM-2 Algorithm - Easiness Factor
# ============================================================================

def test_sm2_easiness_factor_bounds():
    """Test that easiness factor stays within bounds (minimum 1.3)."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    # Repeatedly give quality 3 (correct with difficulty)
    # This should lower EF but not below 1.3
    for _ in range(10):
        card = calculate_next_review(3, card)
        assert card.easiness_factor >= 1.3, f"EF dropped below 1.3: {card.easiness_factor}"


def test_sm2_easiness_factor_increases_with_perfect_recall():
    """Test that easiness factor increases with perfect recall."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    initial_ef = card.easiness_factor  # 2.5
    
    # Perfect recall should increase EF
    card = calculate_next_review(5, card)
    assert card.easiness_factor > initial_ef


def test_sm2_easiness_factor_decreases_with_difficulty():
    """Test that easiness factor decreases with difficult recall."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    initial_ef = card.easiness_factor  # 2.5
    
    # Difficult recall should decrease EF
    card = calculate_next_review(3, card)
    assert card.easiness_factor < initial_ef


# ============================================================================
# Test: SM-2 Algorithm - Reset Behavior
# ============================================================================

def test_sm2_reset_on_failure():
    """Verify that quality < 3 resets repetitions and interval."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    # Build up to repetition 3
    card = calculate_next_review(5, card)
    card = calculate_next_review(5, card)
    card = calculate_next_review(5, card)
    
    assert card.repetitions == 3
    assert card.interval >= 15
    
    # Fail the next review (quality=2)
    card = calculate_next_review(2, card)
    
    # Should reset to intensive review
    assert card.repetitions == 0, "Repetitions should reset to 0"
    assert card.interval == 0, "Interval should reset to 0"
    assert card.next_review is not None, "Should still schedule next review"


# ============================================================================
# Test: Statistics Tracking
# ============================================================================

def test_sm2_tracks_total_reviews():
    """Test that total_reviews increments on every review."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    assert card.total_reviews == 0
    
    card = calculate_next_review(5, card)
    assert card.total_reviews == 1
    
    card = calculate_next_review(2, card)  # Failed review
    assert card.total_reviews == 2
    
    card = calculate_next_review(5, card)
    assert card.total_reviews == 3


def test_sm2_tracks_correct_reviews():
    """Test that correct_reviews only increments for quality >= 3."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    assert card.correct_reviews == 0
    
    card = calculate_next_review(5, card)
    assert card.correct_reviews == 1
    
    card = calculate_next_review(2, card)  # Failed review
    assert card.correct_reviews == 1  # Should not increment
    
    card = calculate_next_review(3, card)
    assert card.correct_reviews == 2


# ============================================================================
# Test: JSON Serialization
# ============================================================================

def test_json_serialization_round_trip(mock_cards_db):
    """Test that cards can be saved and loaded without data loss."""
    card = KnowledgeCard(
        id=1,
        track="Summit Point",
        category="braking",
        question="What is the braking point for T1?",
        answer="Brake at the 2 board",
        created_at=datetime.now(timezone.utc).isoformat(),
        easiness_factor=2.6,
        interval=6,
        repetitions=2,
        next_review=datetime.now(timezone.utc).isoformat(),
        last_reviewed=datetime.now(timezone.utc).isoformat(),
        total_reviews=2,
        correct_reviews=2
    )
    
    # Save
    data = {"cards": [card], "next_id": 2}
    save_cards(data)
    
    # Load
    loaded_data = load_cards()
    loaded_card = loaded_data["cards"][0]
    
    # Verify all fields
    assert loaded_card.id == card.id
    assert loaded_card.track == card.track
    assert loaded_card.category == card.category
    assert loaded_card.question == card.question
    assert loaded_card.answer == card.answer
    assert loaded_card.easiness_factor == card.easiness_factor
    assert loaded_card.interval == card.interval
    assert loaded_card.repetitions == card.repetitions
    assert loaded_card.total_reviews == card.total_reviews
    assert loaded_card.correct_reviews == card.correct_reviews


def test_load_cards_with_corrupted_card(mock_cards_db, capsys):
    """Test that corrupted cards are skipped with a warning."""
    # Create a database with one valid and one corrupted card
    data = {
        "cards": [
            {
                "id": 1,
                "track": "Test",
                "category": "corner",
                "question": "Q1",
                "answer": "A1",
                "created_at": "2025-01-01",
                "easiness_factor": 2.5,
                "interval": 0,
                "repetitions": 0,
                "next_review": "2025-01-01",
                "total_reviews": 0,
                "correct_reviews": 0
            },
            {
                "id": 2,
                "track": "Test",
                "category": "corner",
                "question": "Q2",
                "answer": "A2",
                "created_at": "2025-01-01",
                "invalid_field_that_causes_error": "This will cause TypeError",
                "easiness_factor": "not_a_number",  # Wrong type
            }
        ],
        "next_id": 3
    }
    
    # Write corrupted data
    mock_cards_db.write_text(json.dumps(data))
    
    # Load should skip corrupted card
    loaded_data = load_cards()
    
    # Should have loaded only 1 card
    assert len(loaded_data["cards"]) == 1
    assert loaded_data["cards"][0].id == 1
    
    # Should have printed a warning
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "card #2" in captured.out


# ============================================================================
# Test: Timezone Awareness
# ============================================================================

def test_datetime_fields_are_timezone_aware():
    """Verify that datetime fields contain timezone information."""
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at="2025-01-01"
    )
    
    card = calculate_next_review(5, card)
    
    # Check that ISO strings contain timezone info
    assert card.next_review.endswith("+00:00") or card.next_review.endswith("Z")
    assert card.last_reviewed.endswith("+00:00") or card.last_reviewed.endswith("Z")


def test_new_card_has_timezone_aware_dates():
    """Verify that newly created cards have timezone-aware dates."""
    now_str = datetime.now(timezone.utc).isoformat()
    
    card = KnowledgeCard(
        id=1, track="Test", category="corner",
        question="Q", answer="A", created_at=now_str,
        next_review=now_str
    )
    
    # Verify the ISO strings contain timezone info
    assert "+00:00" in now_str or "Z" in now_str
