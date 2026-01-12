"""Unit tests for Reddit Momentum Formula calculation module."""

import pytest
import pandas as pd
import numpy as np

from src.reddit_momentum_formula import (
    calculate_momentum_score,
    filter_by_stock_universe,
    rank_by_momentum,
    get_top_momentum_picks,
)


class TestCalculateMomentumScore:
    """Tests for calculate_momentum_score function."""

    def test_momentum_score_valid_inputs(self):
        """Should calculate correct momentum score with valid inputs."""
        # sentiment_score = 0.15, comments = 150
        # score = 0.15 * 1000 + log(151) = 150 + 5.02 = 155.02
        result = calculate_momentum_score(sentiment_score=0.15, no_of_comments=150)
        assert result == pytest.approx(155.02, rel=0.01)

    def test_momentum_score_high_sentiment(self):
        """Should handle high positive sentiment."""
        # sentiment_score = 0.30, comments = 200
        # score = 0.30 * 1000 + log(201) = 300 + 5.30 = 305.30
        result = calculate_momentum_score(sentiment_score=0.30, no_of_comments=200)
        assert result == pytest.approx(305.30, rel=0.01)

    def test_momentum_score_low_sentiment(self):
        """Should handle low sentiment."""
        # sentiment_score = 0.05, comments = 50
        # score = 0.05 * 1000 + log(51) = 50 + 3.93 = 53.93
        result = calculate_momentum_score(sentiment_score=0.05, no_of_comments=50)
        assert result == pytest.approx(53.93, rel=0.01)

    def test_momentum_score_negative_sentiment(self):
        """Should handle negative sentiment."""
        # sentiment_score = -0.10, comments = 100
        # score = -0.10 * 1000 + log(101) = -100 + 4.62 = -95.38
        result = calculate_momentum_score(sentiment_score=-0.10, no_of_comments=100)
        assert result == pytest.approx(-95.38, rel=0.01)

    def test_momentum_score_zero_comments(self):
        """Should handle zero comments."""
        # sentiment_score = 0.15, comments = 0
        # score = 0.15 * 1000 + log(1) = 150 + 0 = 150
        result = calculate_momentum_score(sentiment_score=0.15, no_of_comments=0)
        assert result == pytest.approx(150.0, rel=0.01)

    def test_momentum_score_very_high_volume(self):
        """Should apply logarithmic scaling to high comment volumes."""
        # Log scaling prevents spam from dominating
        score_100 = calculate_momentum_score(0.15, 100)
        score_1000 = calculate_momentum_score(0.15, 1000)
        score_10000 = calculate_momentum_score(0.15, 10000)

        # 1000 comments shouldn't be 10x better than 100
        # log(101) ≈ 4.62, log(1001) ≈ 6.91, log(10001) ≈ 9.21
        # Difference should be logarithmic, not linear
        assert score_1000 < score_100 * 1.02  # Not 10x better
        assert score_10000 < score_1000 * 1.04  # Not 10x better

    def test_momentum_score_sentiment_dominates(self):
        """Sentiment should dominate over comment volume."""
        # Low sentiment with high volume vs high sentiment with low volume
        low_sentiment_high_volume = calculate_momentum_score(0.05, 1000)
        high_sentiment_low_volume = calculate_momentum_score(0.25, 10)

        # High sentiment (250) should beat low sentiment (50 + ~7)
        assert high_sentiment_low_volume > low_sentiment_high_volume


class TestFilterByStockUniverse:
    """Tests for filter_by_stock_universe function."""

    def test_filters_to_stock_universe(self):
        """Should filter Reddit data to only include stocks in universe."""
        reddit_data = [
            {"ticker": "NVDA", "no_of_comments": 150, "sentiment": "Bullish", "sentiment_score": 0.15},
            {"ticker": "AAPL", "no_of_comments": 75, "sentiment": "Bullish", "sentiment_score": 0.12},
            {"ticker": "Meme", "no_of_comments": 500, "sentiment": "Bullish", "sentiment_score": 0.20},
        ]
        stock_universe = ["AAPL", "NVDA", "MSFT"]

        result = filter_by_stock_universe(reddit_data, stock_universe)

        assert len(result) == 2
        assert set(result["ticker"].tolist()) == {"AAPL", "NVDA"}
        assert "Meme" not in result["ticker"].tolist()

    def test_case_insensitive_ticker_matching(self):
        """Should match tickers case-insensitively."""
        reddit_data = [
            {"ticker": "nvda", "no_of_comments": 150, "sentiment": "Bullish", "sentiment_score": 0.15},
            {"ticker": "aapl", "no_of_comments": 75, "sentiment": "Bullish", "sentiment_score": 0.12},
        ]
        stock_universe = ["AAPL", "NVDA", "MSFT"]

        result = filter_by_stock_universe(reddit_data, stock_universe)

        assert len(result) == 2
        # Result should have uppercase tickers
        assert result["ticker"].tolist() == ["NVDA", "AAPL"]

    def test_returns_dataframe_with_correct_columns(self):
        """Should return DataFrame with expected columns."""
        reddit_data = [
            {"ticker": "NVDA", "no_of_comments": 150, "sentiment": "Bullish", "sentiment_score": 0.15},
        ]
        stock_universe = ["NVDA", "AAPL"]

        result = filter_by_stock_universe(reddit_data, stock_universe)

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["ticker", "no_of_comments", "sentiment", "sentiment_score"]

    def test_empty_reddit_data(self):
        """Should handle empty Reddit data."""
        result = filter_by_stock_universe([], ["AAPL", "NVDA"])

        assert result.empty
        assert isinstance(result, pd.DataFrame)

    def test_no_matches_in_universe(self):
        """Should return empty DataFrame when no stocks match universe."""
        reddit_data = [
            {"ticker": "MEME1", "no_of_comments": 500, "sentiment": "Bullish", "sentiment_score": 0.20},
            {"ticker": "MEME2", "no_of_comments": 300, "sentiment": "Bullish", "sentiment_score": 0.18},
        ]
        stock_universe = ["AAPL", "NVDA", "MSFT"]

        result = filter_by_stock_universe(reddit_data, stock_universe)

        assert result.empty
        assert isinstance(result, pd.DataFrame)

    def test_all_stocks_match_universe(self):
        """Should include all stocks when all match universe."""
        reddit_data = [
            {"ticker": "AAPL", "no_of_comments": 75, "sentiment": "Bullish", "sentiment_score": 0.12},
            {"ticker": "NVDA", "no_of_comments": 150, "sentiment": "Bullish", "sentiment_score": 0.15},
            {"ticker": "MSFT", "no_of_comments": 50, "sentiment": "Bullish", "sentiment_score": 0.10},
        ]
        stock_universe = ["AAPL", "NVDA", "MSFT"]

        result = filter_by_stock_universe(reddit_data, stock_universe)

        assert len(result) == 3

    def test_preserves_original_data_values(self):
        """Should preserve original sentiment and comment values."""
        reddit_data = [
            {"ticker": "NVDA", "no_of_comments": 150, "sentiment": "Bullish", "sentiment_score": 0.15},
        ]
        stock_universe = ["NVDA"]

        result = filter_by_stock_universe(reddit_data, stock_universe)

        assert result.iloc[0]["no_of_comments"] == 150
        assert result.iloc[0]["sentiment"] == "Bullish"
        assert result.iloc[0]["sentiment_score"] == 0.15


class TestRankByMomentum:
    """Tests for rank_by_momentum function."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            "ticker": ["A", "B", "C", "D", "E"],
            "no_of_comments": [100, 50, 200, 25, 150],
            "sentiment": ["Bullish", "Bullish", "Bullish", "Bearish", "Bullish"],
            "sentiment_score": [0.10, 0.15, 0.20, -0.05, 0.12],
        })

    def test_rank_adds_momentum_score_column(self, sample_df):
        """Should add momentum_score column."""
        result = rank_by_momentum(sample_df)

        assert "momentum_score" in result.columns

    def test_rank_adds_rank_column(self, sample_df):
        """Should add rank column."""
        result = rank_by_momentum(sample_df)

        assert "rank" in result.columns

    def test_rank_calculates_correct_momentum_scores(self, sample_df):
        """Should calculate correct momentum scores."""
        result = rank_by_momentum(sample_df)

        # C: 0.20 * 1000 + log(201) = 200 + 5.30 = 205.30
        c_row = result[result["ticker"] == "C"].iloc[0]
        assert c_row["momentum_score"] == pytest.approx(205.30, rel=0.01)

        # B: 0.15 * 1000 + log(51) = 150 + 3.93 = 153.93
        b_row = result[result["ticker"] == "B"].iloc[0]
        assert b_row["momentum_score"] == pytest.approx(153.93, rel=0.01)

    def test_rank_ranks_by_momentum_score_descending(self, sample_df):
        """Should rank stocks by momentum score (highest = rank 1)."""
        result = rank_by_momentum(sample_df)

        # C should have highest score (0.20 sentiment, 200 comments)
        c_row = result[result["ticker"] == "C"].iloc[0]
        assert c_row["rank"] == 1

        # D should have lowest score (negative sentiment)
        d_row = result[result["ticker"] == "D"].iloc[0]
        assert d_row["rank"] == 5

    def test_rank_sorts_by_momentum_score_descending(self, sample_df):
        """Should sort DataFrame by momentum_score descending."""
        result = rank_by_momentum(sample_df)

        momentum_scores = result["momentum_score"].tolist()
        # Should be in descending order
        assert momentum_scores == sorted(momentum_scores, reverse=True)

    def test_rank_handles_empty_dataframe(self):
        """Should handle empty DataFrame."""
        empty_df = pd.DataFrame(columns=["ticker", "no_of_comments", "sentiment", "sentiment_score"])
        result = rank_by_momentum(empty_df)

        assert result.empty
        assert isinstance(result, pd.DataFrame)

    def test_rank_handles_single_stock(self):
        """Should handle single stock DataFrame."""
        df = pd.DataFrame({
            "ticker": ["NVDA"],
            "no_of_comments": [150],
            "sentiment": ["Bullish"],
            "sentiment_score": [0.15],
        })

        result = rank_by_momentum(df)

        assert len(result) == 1
        assert result.iloc[0]["rank"] == 1

    def test_rank_preserves_original(self, sample_df):
        """Should not modify the original DataFrame."""
        original_columns = sample_df.columns.tolist()
        rank_by_momentum(sample_df)

        assert sample_df.columns.tolist() == original_columns
        assert "momentum_score" not in sample_df.columns


class TestGetTopMomentumPicks:
    """Tests for get_top_momentum_picks function."""

    @pytest.fixture
    def ranked_df(self):
        """Create a ranked DataFrame for testing."""
        df = pd.DataFrame({
            "ticker": ["A", "B", "C", "D", "E", "F", "G"],
            "no_of_comments": [100, 50, 200, 25, 150, 75, 30],
            "sentiment": ["Bullish", "Bullish", "Bullish", "Bearish", "Bullish", "Bullish", "Bearish"],
            "sentiment_score": [0.10, 0.15, 0.20, -0.05, 0.12, 0.08, -0.10],
            "momentum_score": [150.0, 153.0, 205.0, -95.0, 152.0, 148.0, -100.0],
            "rank": [3, 2, 1, 6, 4, 5, 7],
        })
        return df

    def test_get_top_picks_default_n(self, ranked_df):
        """Should return 5 stocks by default."""
        result = get_top_momentum_picks(ranked_df)
        assert len(result) == 5

    def test_get_top_picks_custom_n(self, ranked_df):
        """Should return specified number of stocks."""
        result = get_top_momentum_picks(ranked_df, n=3)
        assert len(result) == 3

    def test_get_top_picks_filters_bearish_stocks(self, ranked_df):
        """Should filter out stocks with bearish sentiment."""
        result = get_top_momentum_picks(ranked_df, n=10)

        # D and G are bearish, should be excluded
        assert "D" not in result["ticker"].tolist()
        assert "G" not in result["ticker"].tolist()

        # Only bullish stocks should be included
        assert all(result["sentiment"] == "Bullish")

    def test_get_top_picks_returns_bullish_only(self, ranked_df):
        """Should only return stocks with bullish sentiment."""
        result = get_top_momentum_picks(ranked_df, n=10)

        for _, row in result.iterrows():
            assert row["sentiment"] == "Bullish"

    def test_get_top_picks_n_larger_than_bullish_count(self, ranked_df):
        """Should return all bullish stocks if n > bullish count."""
        # Only 5 bullish stocks in the fixture
        result = get_top_momentum_picks(ranked_df, n=100)

        assert len(result) == 5  # Only 5 bullish stocks

    def test_get_top_picks_empty_dataframe(self):
        """Should handle empty DataFrame."""
        empty_df = pd.DataFrame(columns=[
            "ticker", "no_of_comments", "sentiment", "sentiment_score", "momentum_score", "rank"
        ])
        result = get_top_momentum_picks(empty_df)

        assert result.empty
        assert isinstance(result, pd.DataFrame)

    def test_get_top_picks_all_bearish(self):
        """Should return empty DataFrame when all stocks are bearish."""
        df = pd.DataFrame({
            "ticker": ["A", "B", "C"],
            "no_of_comments": [100, 50, 200],
            "sentiment": ["Bearish", "Bearish", "Bearish"],
            "sentiment_score": [-0.10, -0.05, -0.15],
            "momentum_score": [-100, -50, -150],
            "rank": [3, 1, 4],
        })

        result = get_top_momentum_picks(df, n=5)

        assert result.empty

    def test_get_top_picks_preserves_columns(self, ranked_df):
        """Should preserve all columns from input."""
        result = get_top_momentum_picks(ranked_df, n=3)

        for col in ranked_df.columns:
            assert col in result.columns

    def test_get_top_picks_returns_copy(self, ranked_df):
        """Should return a copy, not a view."""
        result = get_top_momentum_picks(ranked_df, n=3)
        result["new_col"] = 1

        assert "new_col" not in ranked_df.columns

    def test_get_top_picks_returns_highest_momentum_bullish(self, ranked_df):
        """Should return bullish stocks with highest momentum scores."""
        result = get_top_momentum_picks(ranked_df, n=3)

        # Should get C, B, E (top 3 bullish by momentum score)
        top_tickers = result["ticker"].tolist()
        assert "C" in top_tickers  # Score 205.0, rank 1
        assert "B" in top_tickers  # Score 153.0, rank 2
        assert "E" in top_tickers  # Score 152.0, rank 4 (D is rank 6 but bearish)
