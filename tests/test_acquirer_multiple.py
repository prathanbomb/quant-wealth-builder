"""Unit tests for Acquirer's Multiple module."""

import pytest
import pandas as pd

from src.acquirer_multiple import (
    calculate_acquirer_multiple,
    calculate_acquirer_from_dict,
    rank_by_acquirer_multiple,
    get_top_acquirer_picks,
)


class TestCalculateAcquirerMultiple:
    """Tests for calculate_acquirer_multiple function."""

    def test_basic_calculation(self):
        """Should calculate Acquirer's Multiple correctly."""
        # EV = 1000, EBIT = 100
        # Multiple = 1000 / 100 = 10
        result = calculate_acquirer_multiple(1000, 100)
        assert result == 10.0

    def test_very_cheap_stock(self):
        """Should calculate very low multiple (deep value)."""
        # EV = 250, EBIT = 100
        # Multiple = 250 / 100 = 2.5 (very cheap)
        result = calculate_acquirer_multiple(250, 100)
        assert result == 2.5

    def test_expensive_stock(self):
        """Should calculate high multiple."""
        # EV = 2000, EBIT = 100
        # Multiple = 2000 / 100 = 20 (expensive)
        result = calculate_acquirer_multiple(2000, 100)
        assert result == 20.0

    def test_returns_none_for_negative_ebit(self):
        """Should return None for negative EBIT (losing money)."""
        result = calculate_acquirer_multiple(1000, -100)
        assert result is None

    def test_returns_none_for_zero_ebit(self):
        """Should return None for zero EBIT (avoid division by zero)."""
        result = calculate_acquirer_multiple(1000, 0)
        assert result is None

    def test_returns_none_for_negative_ev(self):
        """Should return None for negative Enterprise Value."""
        result = calculate_acquirer_multiple(-1000, 100)
        assert result is None

    def test_returns_none_for_none_ev(self):
        """Should return None for None Enterprise Value."""
        result = calculate_acquirer_multiple(None, 100)
        assert result is None

    def test_returns_none_for_none_ebit(self):
        """Should return None for None EBIT."""
        result = calculate_acquirer_multiple(1000, None)
        assert result is None

    def test_returns_none_for_both_none(self):
        """Should return None when both inputs are None."""
        result = calculate_acquirer_multiple(None, None)
        assert result is None

    def test_handles_large_values(self):
        """Should handle very large values (e.g., large caps)."""
        # EV = 2.9 trillion, EBIT = 100 billion
        # Multiple = 2,900,000,000,000 / 100,000,000,000 = 29
        result = calculate_acquirer_multiple(2_900_000_000_000, 100_000_000_000)
        assert result == pytest.approx(29.0, rel=0.01)

    def test_handles_small_values(self):
        """Should handle small decimal values."""
        result = calculate_acquirer_multiple(500.5, 50.5)
        assert result == pytest.approx(9.91, rel=0.01)


class TestCalculateAcquirerFromDict:
    """Tests for calculate_acquirer_from_dict function."""

    def test_calculates_from_dict(self):
        """Should calculate Acquirer's Multiple from stock data dictionary."""
        data = {
            "enterprise_value": 1000,
            "ebit": 100,
        }
        result = calculate_acquirer_from_dict(data)
        assert result == 10.0

    def test_returns_none_for_missing_ev(self):
        """Should return None when Enterprise Value is missing."""
        data = {
            "ebit": 100,
        }
        result = calculate_acquirer_from_dict(data)
        assert result is None

    def test_returns_none_for_missing_ebit(self):
        """Should return None when EBIT is missing."""
        data = {
            "enterprise_value": 1000,
        }
        result = calculate_acquirer_from_dict(data)
        assert result is None

    def test_handles_negative_ebit_in_dict(self):
        """Should return None for negative EBIT in dict."""
        data = {
            "enterprise_value": 1000,
            "ebit": -100,
        }
        result = calculate_acquirer_from_dict(data)
        assert result is None


class TestRankByAcquirerMultiple:
    """Tests for rank_by_acquirer_multiple function."""

    def test_ranks_stocks_by_multiple_ascending(self):
        """Should rank stocks by Acquirer's Multiple ascending (lower is better)."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 500, "ebit": 100},
            # A: Multiple = 5 (cheapest)
            {"symbol": "B", "enterprise_value": 1000, "ebit": 100},
            # B: Multiple = 10
            {"symbol": "C", "enterprise_value": 2000, "ebit": 100},
            # C: Multiple = 20 (most expensive)
        ])

        result = rank_by_acquirer_multiple(df)

        assert len(result) == 3
        assert "acquirer_multiple" in result.columns
        assert "rank_acquirer" in result.columns

        # Stock A should be first (lowest multiple)
        assert result.iloc[0]["symbol"] == "A"
        assert result.iloc[0]["acquirer_multiple"] == 5.0
        assert result.iloc[0]["rank_acquirer"] == 1

        # Stock B should be second
        assert result.iloc[1]["symbol"] == "B"
        assert result.iloc[1]["acquirer_multiple"] == 10.0
        assert result.iloc[1]["rank_acquirer"] == 2

        # Stock C should be last (highest multiple)
        assert result.iloc[2]["symbol"] == "C"
        assert result.iloc[2]["acquirer_multiple"] == 20.0
        assert result.iloc[2]["rank_acquirer"] == 3

    def test_excludes_stocks_with_negative_ebit(self):
        """Should exclude stocks with negative EBIT (no valid multiple)."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 1000, "ebit": 100},
            {"symbol": "B", "enterprise_value": 1000, "ebit": -100},
            {"symbol": "C", "enterprise_value": 1000, "ebit": 50},
        ])

        result = rank_by_acquirer_multiple(df)

        # Only A and C should be included (B has negative EBIT)
        assert len(result) == 2
        assert "B" not in result["symbol"].values

    def test_excludes_stocks_with_zero_ebit(self):
        """Should exclude stocks with zero EBIT."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 1000, "ebit": 100},
            {"symbol": "B", "enterprise_value": 1000, "ebit": 0},
        ])

        result = rank_by_acquirer_multiple(df)

        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "A"

    def test_excludes_stocks_with_negative_ev(self):
        """Should exclude stocks with negative Enterprise Value."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 1000, "ebit": 100},
            {"symbol": "B", "enterprise_value": -1000, "ebit": 100},
        ])

        result = rank_by_acquirer_multiple(df)

        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "A"

    def test_excludes_stocks_with_missing_data(self):
        """Should exclude stocks with missing required data."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 1000, "ebit": 100},
            {"symbol": "B", "enterprise_value": None, "ebit": 100},
            {"symbol": "C", "enterprise_value": 1000, "ebit": None},
            {"symbol": "D", "enterprise_value": None, "ebit": None},
        ])

        result = rank_by_acquirer_multiple(df)

        # Only A should be included
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "A"

    def test_handles_ties_deterministically(self):
        """Should handle ties with method='first' for consistent ordering."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 1000, "ebit": 100},
            # A: Multiple = 10
            {"symbol": "B", "enterprise_value": 500, "ebit": 50},
            # B: Multiple = 10 (tie)
            {"symbol": "C", "enterprise_value": 1500, "ebit": 100},
            # C: Multiple = 15
        ])

        result = rank_by_acquirer_multiple(df)

        assert len(result) == 3
        # A and B should both have multiple of 10 but different ranks
        assert result.iloc[0]["acquirer_multiple"] == 10.0
        assert result.iloc[1]["acquirer_multiple"] == 10.0
        # Ranks should be different even for ties
        assert result.iloc[0]["rank_acquirer"] != result.iloc[1]["rank_acquirer"]

    def test_returns_empty_dataframe_when_no_valid_stocks(self):
        """Should return empty DataFrame when no valid stocks."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 1000, "ebit": -100},
            {"symbol": "B", "enterprise_value": 1000, "ebit": 0},
        ])

        result = rank_by_acquirer_multiple(df)

        assert result.empty

    def test_calculates_multiple_correctly(self):
        """Should calculate Acquirer's Multiple for each stock."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 800, "ebit": 100},
        ])

        result = rank_by_acquirer_multiple(df)

        # Multiple = 800 / 100 = 8
        assert result.iloc[0]["acquirer_multiple"] == 8.0

    def test_sorts_ascending(self):
        """Should sort stocks in ascending order by multiple."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 2000, "ebit": 100},  # 20x
            {"symbol": "B", "enterprise_value": 500, "ebit": 100},   # 5x
            {"symbol": "C", "enterprise_value": 1000, "ebit": 100},  # 10x
        ])

        result = rank_by_acquirer_multiple(df)

        # Should be sorted: B (5x), C (10x), A (20x)
        assert list(result["symbol"]) == ["B", "C", "A"]


class TestGetTopAcquirerPicks:
    """Tests for get_top_acquirer_picks function."""

    def test_returns_top_n_stocks(self):
        """Should return top N stocks (lowest multiples)."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 500, "ebit": 100,
             "acquirer_multiple": 5.0, "rank_acquirer": 1},
            {"symbol": "B", "enterprise_value": 1000, "ebit": 100,
             "acquirer_multiple": 10.0, "rank_acquirer": 2},
            {"symbol": "C", "enterprise_value": 2000, "ebit": 100,
             "acquirer_multiple": 20.0, "rank_acquirer": 3},
        ])

        result = get_top_acquirer_picks(df, n=2)

        assert len(result) == 2
        assert list(result["symbol"]) == ["A", "B"]

    def test_returns_all_when_n_exceeds_length(self):
        """Should return all stocks when n exceeds DataFrame length."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 1000, "ebit": 100,
             "acquirer_multiple": 10.0, "rank_acquirer": 1},
        ])

        result = get_top_acquirer_picks(df, n=10)

        assert len(result) == 1

    def test_returns_copy(self):
        """Should return a copy, not a view."""
        df = pd.DataFrame([
            {"symbol": "A", "enterprise_value": 1000, "ebit": 100,
             "acquirer_multiple": 10.0, "rank_acquirer": 1},
        ])

        result = get_top_acquirer_picks(df, n=1)
        result.loc[0, "symbol"] = "X"

        assert df.iloc[0]["symbol"] == "A"  # Original unchanged

    def test_default_n_is_5(self):
        """Default n should be 5."""
        df = pd.DataFrame([
            {"symbol": f"S{i}", "enterprise_value": i * 1000, "ebit": 100,
             "acquirer_multiple": i * 10.0, "rank_acquirer": i}
            for i in range(1, 11)
        ])

        result = get_top_acquirer_picks(df)

        assert len(result) == 5
