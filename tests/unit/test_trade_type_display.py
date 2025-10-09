"""Unit tests for trade type display name functionality"""
import pytest

from utils.enums import TradeTypeEnums


class TestTradeTypeDisplayNames:
    """Test trade type display name methods"""

    def test_get_display_name_crypto_fiat(self):
        """Test display name for CryptoToFiat trade"""
        result = TradeTypeEnums.get_display_name("CryptoToFiat")
        assert result == "💰 Crypto → Fiat Trade"

    def test_get_display_name_crypto_crypto(self):
        """Test display name for CryptoToCrypto trade"""
        result = TradeTypeEnums.get_display_name("CryptoToCrypto")
        assert result == "🔄 Crypto Swap"

    def test_get_display_name_crypto_product(self):
        """Test display name for CryptoToProduct trade"""
        result = TradeTypeEnums.get_display_name("CryptoToProduct")
        assert result == "🛍️ Buy Goods with Crypto"

    def test_get_display_name_market_shop(self):
        """Test display name for MarketShop trade"""
        result = TradeTypeEnums.get_display_name("MarketShop")
        assert result == "🏪 Marketplace Listing"

    def test_get_display_name_unknown(self):
        """Test display name for unknown trade type returns original value"""
        result = TradeTypeEnums.get_display_name("UnknownType")
        assert result == "UnknownType"

    def test_get_short_display_name_crypto_fiat(self):
        """Test short display name for CryptoToFiat trade"""
        result = TradeTypeEnums.get_short_display_name("CryptoToFiat")
        assert result == "Crypto → Fiat"

    def test_get_short_display_name_crypto_crypto(self):
        """Test short display name for CryptoToCrypto trade"""
        result = TradeTypeEnums.get_short_display_name("CryptoToCrypto")
        assert result == "Crypto Swap"

    def test_get_short_display_name_crypto_product(self):
        """Test short display name for CryptoToProduct trade"""
        result = TradeTypeEnums.get_short_display_name("CryptoToProduct")
        assert result == "Buy Goods"

    def test_get_short_display_name_market_shop(self):
        """Test short display name for MarketShop trade"""
        result = TradeTypeEnums.get_short_display_name("MarketShop")
        assert result == "Marketplace"

    def test_get_short_display_name_unknown(self):
        """Test short display name for unknown trade type returns original value"""
        result = TradeTypeEnums.get_short_display_name("UnknownType")
        assert result == "UnknownType"

    def test_display_names_contain_emojis(self):
        """Test that full display names contain emojis"""
        display_names = [
            TradeTypeEnums.get_display_name("CryptoToFiat"),
            TradeTypeEnums.get_display_name("CryptoToCrypto"),
            TradeTypeEnums.get_display_name("CryptoToProduct"),
            TradeTypeEnums.get_display_name("MarketShop"),
        ]

        for name in display_names:
            # Check that each display name starts with an emoji (unicode character)
            assert any(
                ord(c) > 127 for c in name
            ), f"Display name '{name}' should contain emoji"

    def test_short_names_no_emojis(self):
        """Test that short display names don't contain emojis"""
        short_names = [
            TradeTypeEnums.get_short_display_name("CryptoToFiat"),
            TradeTypeEnums.get_short_display_name("CryptoToCrypto"),
            TradeTypeEnums.get_short_display_name("CryptoToProduct"),
            TradeTypeEnums.get_short_display_name("MarketShop"),
        ]

        # Short names should not start with emojis (they should start with ASCII letters)
        for name in short_names:
            assert name[0].isalpha() or name[0] in [
                "→",
                "←",
            ], f"Short name '{name}' should not start with emoji"

    def test_all_enum_values_have_display_names(self):
        """Test that all TradeTypeEnums values have display names"""
        for trade_type_enum in TradeTypeEnums:
            trade_type_value = trade_type_enum.value

            # Get display names
            display_name = TradeTypeEnums.get_display_name(trade_type_value)
            short_name = TradeTypeEnums.get_short_display_name(trade_type_value)

            # Both should return something other than the raw value
            assert (
                display_name != trade_type_value
            ), f"Missing display name for {trade_type_value}"
            assert (
                short_name != trade_type_value
            ), f"Missing short display name for {trade_type_value}"

    def test_display_names_are_user_friendly(self):
        """Test that display names are more readable than raw values"""
        test_cases = [
            ("CryptoToFiat", "→"),  # Should contain arrow
            ("CryptoToCrypto", "Swap"),  # Should mention swap
            ("CryptoToProduct", "Goods"),  # Should mention goods
            ("MarketShop", "Marketplace"),  # Should mention marketplace
        ]

        for raw_value, expected_substring in test_cases:
            display_name = TradeTypeEnums.get_display_name(raw_value)
            assert (
                expected_substring in display_name
            ), f"Display name '{display_name}' should contain '{expected_substring}'"

    def test_display_name_backwards_compatibility(self):
        """Test that method handles None and empty strings gracefully"""
        # Test with empty string
        result = TradeTypeEnums.get_display_name("")
        assert result == ""

        # Test short name with empty string
        result = TradeTypeEnums.get_short_display_name("")
        assert result == ""
