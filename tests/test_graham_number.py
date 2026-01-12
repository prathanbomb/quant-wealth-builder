"""Unit tests for Graham Number module."""

import pytest
import pandas as pd

from src.graham_number import (
    calculate_graham_number,
    calculate_margin_of_safety,
    calculate_graham_from_dict,
    rank_by_margin_of_safety,
    get_top_graham_picks,
)


class TestCalculateGrahamNumber:
    """Tests for calculate_graham_number function."""

    def test_basic_calculation(self):
        """Should calculate Graham Number correctly."""
        # EPS = 4, BVPS = 10
        # Graham Number = sqrt(22.5 * 4 * 10) = sqrt(900) = 30
        result = calculate_graham_number(4, 10)
        assert result == pytest.approx(30.0)

    def test_rounded_values(self):
        """Should handle non-integer values."""
        # EPS = 6.05, BVPS = 4.25
        # Graham Number = sqrt(22.5 * 6.05 * 4.25) = sqrt(577.30625) ≈ 24.03
        result = calculate_graham_number(6.05, 4.25)
        assert result == pytest.approx(24.03, rel=0.01)

    def test_returns_none_for_negative_eps(self):
        """Should return None for negative EPS."""
        result = calculate_graham_number(-2, 10)
        assert result is None

    def test_returns_none_for_zero_eps(self):
        """Should return None for zero EPS."""
        result = calculate_graham_number(0, 10)
        assert result is None

    def test_returns_none_for_negative_bvps(self):
        """Should return None for negative BVPS."""
        result = calculate_graham_number(4, -10)
        assert result is None

    def test_returns_none_for_zero_bvps(self):
        """Should return None for zero BVPS."""
        result = calculate_graham_number(4, 0)
        assert result is None

    def test_returns_none_for_none_eps(self):
        """Should return None for None EPS."""
        result = calculate_graham_number(None, 10)
        assert result is None

    def test_returns_none_for_none_bvps(self):
        """Should return None for None BVPS."""
        result = calculate_graham_number(4, None)
        assert result is None

    def test_returns_none_for_both_none(self):
        """Should return None when both inputs are None."""
        result = calculate_graham_number(None, None)
        assert result is None


class TestCalculateMarginOfSafety:
    """Tests for calculate_margin_of_safety function."""

    def test_positive_margin_undervalued(self):
        """Should calculate positive margin for undervalued stock."""
        # Graham Number = 30, Price = 20
        # Margin = (30 - 20) / 30 * 100 = 33.33%
        result = calculate_margin_of_safety(30, 20)
        assert result == pytest.approx(33.33, rel=0.01)

    def test_negative_margin_overvalued(self):
        """Should calculate negative margin for overvalued stock."""
        # Graham Number = 30, Price = 40
        # Margin = (30 - 40) / 30 * 100 = -33.33%
        result = calculate_margin_of_safety(30, 40)
        assert result == pytest.approx(-33.33, rel=0.01)

    def test_zero_margin_at_fair_value(self):
        """Should return 0 when price equals Graham Number."""
        result = calculate_margin_of_safety(30, 30)
        assert result == 0

    def test_returns_none_for_none_graham_number(self):
        """Should return None for None Graham Number."""
        result = calculate_margin_of_safety(None, 20)
        assert result is None

    def test_returns_none_for_none_price(self):
        """Should return None for None price."""
        result = calculate_margin_of_safety(30, None)
        assert result is None

    def test_returns_none_for_zero_graham_number(self):
        """Should return None for zero Graham Number (avoid division by zero)."""
        result = calculate_margin_of_safety(0, 20)
        assert result is None

    def test_handles_large_values(self):
        """Should handle large price values."""
        result = calculate_margin_of_safety(100, 150)
        assert result == pytest.approx(-50, rel=0.01)

    def test_handles_small_positive_margin(self):
        """Should handle small positive margins."""
        result = calculate_margin_of_safety(100, 99)
        assert result == pytest.approx(1, rel=0.01)


class TestCalculateGrahamFromDict:
    """Tests for calculate_graham_from_dict function."""

    def test_calculates_from_dict(self):
        """Should calculate both values from stock data dictionary."""
        data = {
            "eps": 4,
            "book_value_per_share": 10,
            "price": 20,
        }
        graham, margin = calculate_graham_from_dict(data)

        # Graham = sqrt(22.5 * 4 * 10) = 30
        assert graham == pytest.approx(30.0)
        # Margin = (30 - 20) / 30 * 100 = 33.33%
        assert margin == pytest.approx(33.33, rel=0.01)

    def test_returns_none_for_missing_eps(self):
        """Should return None when EPS is missing."""
        data = {
            "book_value_per_share": 10,
            "price": 20,
        }
        graham, margin = calculate_graham_from_dict(data)

        assert graham is None
        assert margin is None

    def test_returns_none_for_missing_bvps(self):
        """Should return None when BVPS is missing."""
        data = {
            "eps": 4,
            "price": 20,
        }
        graham, margin = calculate_graham_from_dict(data)

        assert graham is None
        assert margin is None

    def test_returns_none_for_missing_price(self):
        """Should calculate Graham Number but margin is None when price is missing."""
        data = {
            "eps": 4,
            "book_value_per_share": 10,
        }
        graham, margin = calculate_graham_from_dict(data)

        assert graham is not None
        assert margin is None

    def test_handles_negative_eps(self):
        """Should return None for negative EPS."""
        data = {
            "eps": -2,
            "book_value_per_share": 10,
            "price": 20,
        }
        graham, margin = calculate_graham_from_dict(data)

        assert graham is None
        assert margin is None


class TestRankByMarginOfSafety:
    """Tests for rank_by_margin_of_safety function."""

    def test_ranks_stocks_by_margin(self):
        """Should rank stocks by margin of safety descending."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20},
            # A: Graham = 30, Margin = 33.33%
            {"symbol": "B", "eps": 2, "book_value_per_share": 5, "price": 15},
            # B: Graham = 15, Margin = 0%
            {"symbol": "C", "eps": 6, "book_value_per_share": 15, "price": 50},
            # C: Graham = 45, Margin = -11.11% (overvalued)
        ])

        result = rank_by_margin_of_safety(df)

        assert len(result) == 3
        assert "graham_number" in result.columns
        assert "margin_of_safety" in result.columns
        assert "rank_graham" in result.columns

        # Stock A should be first (highest positive margin)
        assert result.iloc[0]["symbol"] == "A"
        assert result.iloc[0]["margin_of_safety"] == pytest.approx(33.33, rel=0.01)
        assert result.iloc[0]["rank_graham"] == 1

        # Stock B should be second (0% margin)
        assert result.iloc[1]["symbol"] == "B"
        assert result.iloc[1]["margin_of_safety"] == pytest.approx(0, rel=0.01)
        assert result.iloc[1]["rank_graham"] == 2

        # Stock C should be last (negative margin)
        assert result.iloc[2]["symbol"] == "C"
        assert result.iloc[2]["margin_of_safety"] == pytest.approx(-11.11, rel=0.01)
        assert result.iloc[2]["rank_graham"] == 3

    def test_excludes_stocks_with_negative_eps(self):
        """Should exclude stocks with negative EPS (no Graham Number)."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20},
            {"symbol": "B", "eps": -2, "book_value_per_share": 10, "price": 20},
            {"symbol": "C", "eps": 3, "book_value_per_share": 8, "price": 15},
        ])

        result = rank_by_margin_of_safety(df)

        # Only A and C should be included (B has negative EPS)
        assert len(result) == 2
        assert "B" not in result["symbol"].values

    def test_excludes_stocks_with_zero_eps(self):
        """Should exclude stocks with zero EPS (no Graham Number)."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20},
            {"symbol": "B", "eps": 0, "book_value_per_share": 10, "price": 20},
        ])

        result = rank_by_margin_of_safety(df)

        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "A"

    def test_excludes_stocks_with_negative_bvps(self):
        """Should exclude stocks with negative BVPS (no Graham Number)."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20},
            {"symbol": "B", "eps": 4, "book_value_per_share": -5, "price": 20},
        ])

        result = rank_by_margin_of_safety(df)

        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "A"

    def test_excludes_stocks_with_missing_data(self):
        """Should exclude stocks with missing required data."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20},
            {"symbol": "B", "eps": None, "book_value_per_share": 10, "price": 20},
            {"symbol": "C", "eps": 4, "book_value_per_share": None, "price": 20},
            {"symbol": "D", "eps": 4, "book_value_per_share": 10, "price": None},
        ])

        result = rank_by_margin_of_safety(df)

        # Only A should be included
        assert len(result) == 1
        assert result.iloc[0]["symbol"] == "A"

    def test_handles_ties_deterministically(self):
        """Should handle ties with method='first' for consistent ordering."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20},
            # A: Graham = 30, Margin = 33.33%
            {"symbol": "B", "eps": 9, "book_value_per_share": 5, "price": 15},
            # B: Graham = sqrt(22.5*9*5) = 31.82, Margin = (31.82-15)/31.82 = 52.86%
            {"symbol": "C", "eps": 4, "book_value_per_share": 10, "price": 20},
            # C: Same as A - Graham = 30, Margin = 33.33%
        ])

        result = rank_by_margin_of_safety(df)

        assert len(result) == 3
        # B should be first (highest margin)
        assert result.iloc[0]["symbol"] == "B"
        # A and C should have different ranks even with same margin
        assert result.iloc[1]["rank_graham"] != result.iloc[2]["rank_graham"]

    def test_returns_empty_dataframe_when_no_valid_stocks(self):
        """Should return empty DataFrame when no valid stocks."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": -2, "book_value_per_share": 10, "price": 20},
            {"symbol": "B", "eps": 4, "book_value_per_share": -5, "price": 20},
        ])

        result = rank_by_margin_of_safety(df)

        assert result.empty

    def test_calculates_graham_number_correctly(self):
        """Should calculate Graham Number for each stock."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20},
        ])

        result = rank_by_margin_of_safety(df)

        # Graham = sqrt(22.5 * 4 * 10) = 30
        assert result.iloc[0]["graham_number"] == pytest.approx(30.0)


class TestGetTopGrahamPicks:
    """Tests for get_top_graham_picks function."""

    def test_returns_top_n_stocks(self):
        """Should return top N stocks by margin of safety."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20, "graham_number": 30, "margin_of_safety": 33.33, "rank_graham": 1},
            {"symbol": "B", "eps": 2, "book_value_per_share": 5, "price": 15, "graham_number": 15, "margin_of_safety": 0, "rank_graham": 2},
            {"symbol": "C", "eps": 6, "book_value_per_share": 15, "price": 40, "graham_number": 45, "margin_of_safety": -11.11, "rank_graham": 3},
        ])

        result = get_top_graham_picks(df, n=2)

        assert len(result) == 2
        assert list(result["symbol"]) == ["A", "B"]

    def test_returns_all_when_n_exceeds_length(self):
        """Should return all stocks when n exceeds DataFrame length."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20, "graham_number": 30, "margin_of_safety": 33.33, "rank_graham": 1},
        ])

        result = get_top_graham_picks(df, n=10)

        assert len(result) == 1

    def test_returns_copy(self):
        """Should return a copy, not a view."""
        df = pd.DataFrame([
            {"symbol": "A", "eps": 4, "book_value_per_share": 10, "price": 20, "graham_number": 30, "margin_of_safety": 33.33, "rank_graham": 1},
        ])

        result = get_top_graham_picks(df, n=1)
        result.loc[0, "symbol"] = "X"

        assert df.iloc[0]["symbol"] == "A"  # Original unchanged

    def test_default_n_is_5(self):
        """Default n should be 5."""
        df = pd.DataFrame([
            {"symbol": f"S{i}", "eps": i, "book_value_per_share": i * 2, "price": i * 2.5,
             "graham_number": i * 3, "margin_of_safety": i, "rank_graham": i}
            for i in range(1, 11)
        ])

        result = get_top_graham_picks(df)

        assert len(result) == 5
