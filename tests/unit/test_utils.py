"""Unit tests for shared.utils — utility functions."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from shared.utils import (  # noqa: E402
    clean_text,
    extract_keywords,
    generate_id,
    normalize_address_street,
    normalize_business_name,
    normalize_phone,
)


# ---------------------------------------------------------------------------
# normalize_phone
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizePhone:
    def test_parentheses_format(self):
        assert normalize_phone("(713) 555-1234") == "+17135551234"

    def test_dashes_only(self):
        assert normalize_phone("713-555-1234") == "+17135551234"

    def test_plain_digits_10(self):
        assert normalize_phone("7135551234") == "+17135551234"

    def test_with_country_code(self):
        assert normalize_phone("+17135551234") == "+17135551234"

    def test_with_1_prefix(self):
        assert normalize_phone("17135551234") == "+17135551234"

    def test_invalid_too_short(self):
        assert normalize_phone("555") == ""

    def test_invalid_letters(self):
        assert normalize_phone("call-me-now") == ""

    def test_empty_string(self):
        assert normalize_phone("") == ""

    def test_none_input(self):
        assert normalize_phone(None) == ""  # type: ignore[arg-type]

    def test_whitespace_only(self):
        assert normalize_phone("   ") == ""

    def test_international_format_with_dots(self):
        assert normalize_phone("713.555.1234") == "+17135551234"

    def test_spaces_format(self):
        assert normalize_phone("713 555 1234") == "+17135551234"


# ---------------------------------------------------------------------------
# normalize_address_street
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeAddressStreet:
    def test_full_address_with_abbreviations(self):
        result = normalize_address_street("123 MAIN STREET APT 4")
        assert result == "123 Main St Apt 4"

    def test_directional_abbreviations(self):
        result = normalize_address_street("456 NORTH ELM AVENUE")
        assert result == "456 N Elm Ave"

    def test_boulevard(self):
        result = normalize_address_street("789 SUNSET BOULEVARD")
        assert result == "789 Sunset Blvd"

    def test_suite(self):
        result = normalize_address_street("100 MAIN STREET SUITE 200")
        assert result == "100 Main St Ste 200"

    def test_empty_string(self):
        assert normalize_address_street("") == ""

    def test_none_input(self):
        assert normalize_address_street(None) == ""  # type: ignore[arg-type]

    def test_whitespace_only(self):
        assert normalize_address_street("   ") == ""

    def test_already_abbreviated(self):
        result = normalize_address_street("123 Main St")
        assert result == "123 Main St"

    def test_periods_and_commas_stripped(self):
        result = normalize_address_street("123 Main Street., Houston,")
        # "Street." -> lower "street." -> rstrip ".,": "street" -> "St"
        # "Houston," -> lower "houston," -> rstrip ".,": "houston" -> not in abbreviations -> .title() => "Houston"
        assert "St" in result


# ---------------------------------------------------------------------------
# normalize_business_name
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestNormalizeBusinessName:
    def test_llc_suffix(self):
        name, entity = normalize_business_name("SMITH PLUMBING LLC")
        assert name == "Smith Plumbing"
        assert entity == "LLC"

    def test_inc_suffix(self):
        name, entity = normalize_business_name("ACME ELECTRIC INC")
        assert name == "Acme Electric"
        assert entity == "INC"

    def test_corp_suffix(self):
        name, entity = normalize_business_name("BIG BUILDER CORP")
        assert name == "Big Builder"
        assert entity == "CORP"

    def test_llc_with_period(self):
        name, entity = normalize_business_name("PACIFIC PLUMBING LLC.")
        assert name == "Pacific Plumbing"
        assert entity == "LLC"

    def test_comma_separated_entity(self):
        name, entity = normalize_business_name("SUNSHINE BUILDERS, CORP")
        assert name == "Sunshine Builders"
        assert entity == "CORP"

    def test_no_entity_type(self):
        name, entity = normalize_business_name("TOP TIER ROOFING")
        assert name == "Top Tier Roofing"
        assert entity == ""

    def test_empty_string(self):
        name, entity = normalize_business_name("")
        assert name == ""
        assert entity == ""

    def test_none_input(self):
        name, entity = normalize_business_name(None)  # type: ignore[arg-type]
        assert name == ""
        assert entity == ""

    def test_whitespace_only(self):
        name, entity = normalize_business_name("   ")
        assert name == ""
        assert entity == ""

    def test_extra_whitespace_collapsed(self):
        name, entity = normalize_business_name("  SMITH   PLUMBING   LLC  ")
        assert name == "Smith Plumbing"
        assert entity == "LLC"

    def test_dba_suffix(self):
        name, entity = normalize_business_name("JONES CONSTRUCTION DBA")
        assert name == "Jones Construction"
        assert entity == "DBA"

    def test_title_case_result(self):
        name, _ = normalize_business_name("ALL CAPS NAME")
        assert name == "All Caps Name"


# ---------------------------------------------------------------------------
# generate_id
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestGenerateId:
    def test_deterministic(self):
        id1 = generate_id("chicago", "BLD-001")
        id2 = generate_id("chicago", "BLD-001")
        assert id1 == id2

    def test_24_hex_chars(self):
        result = generate_id("a", "b", "c")
        assert len(result) == 24
        assert all(c in "0123456789abcdef" for c in result)

    def test_different_inputs_different_ids(self):
        id1 = generate_id("a", "b")
        id2 = generate_id("a", "c")
        assert id1 != id2

    def test_case_insensitive(self):
        """Parts are lowered, so case should not matter."""
        id1 = generate_id("Chicago", "BLD-001")
        id2 = generate_id("chicago", "BLD-001")
        assert id1 == id2

    def test_whitespace_stripped(self):
        id1 = generate_id("  chicago  ", "  BLD-001  ")
        id2 = generate_id("chicago", "BLD-001")
        assert id1 == id2

    def test_empty_parts_filtered(self):
        """Empty parts are excluded from the hash."""
        id1 = generate_id("a", "", "b")
        id2 = generate_id("a", "b")
        assert id1 == id2

    def test_single_part(self):
        result = generate_id("only-one")
        assert len(result) == 24


# ---------------------------------------------------------------------------
# extract_keywords
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestExtractKeywords:
    def test_basic_extraction(self):
        keywords = extract_keywords("Install new electrical panel in building")
        assert "install" in keywords
        assert "electrical" in keywords
        assert "panel" in keywords
        assert "building" in keywords

    def test_short_words_excluded(self):
        """Words shorter than 3 characters are filtered out."""
        keywords = extract_keywords("A to B in the end")
        assert "to" not in keywords
        assert "in" not in keywords
        assert "end" in keywords
        assert "the" in keywords  # 3 chars, included

    def test_duplicates_removed(self):
        keywords = extract_keywords("test test test again")
        assert keywords.count("test") == 1

    def test_empty_string(self):
        assert extract_keywords("") == []

    def test_none_input(self):
        assert extract_keywords(None) == []  # type: ignore[arg-type]

    def test_numbers_included(self):
        keywords = extract_keywords("Install 200 amp panel")
        assert "200" in keywords
        assert "amp" in keywords

    def test_special_chars_stripped(self):
        keywords = extract_keywords("$500,000 building-permit #1234")
        assert "500" in keywords
        assert "000" in keywords
        assert "1234" in keywords

    def test_case_lowered(self):
        keywords = extract_keywords("ELECTRICAL Panel INSTALL")
        assert "electrical" in keywords
        assert "panel" in keywords
        assert "install" in keywords


# ---------------------------------------------------------------------------
# clean_text
# ---------------------------------------------------------------------------
@pytest.mark.unit
class TestCleanText:
    def test_strips_and_collapses(self):
        assert clean_text("  hello   world  ") == "hello world"

    def test_empty_string(self):
        assert clean_text("") == ""

    def test_none_input(self):
        assert clean_text(None) == ""  # type: ignore[arg-type]

    def test_tabs_and_newlines(self):
        assert clean_text("hello\t\nworld") == "hello world"
