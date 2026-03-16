import pytest
from app.models.outline import Outline, Section


def test_section_defaults():
    section = Section(title="Introduction", key_points=["Hook", "Context"])
    assert section.draft is None
    assert section.approved is False
    assert section.sources == []


def test_section_sources_roundtrip_json():
    section = Section(
        title="Research",
        key_points=["Fact A"],
        sources=["https://example.com/a", "https://example.com/b"],
    )
    restored = Section.model_validate_json(section.model_dump_json())
    assert restored.sources == ["https://example.com/a", "https://example.com/b"]


def test_section_roundtrip_json():
    section = Section(
        title="Introduction",
        key_points=["Hook", "Context"],
        draft="Here is the intro.",
        approved=True,
    )
    restored = Section.model_validate_json(section.model_dump_json())
    assert restored == section


def test_outline_roundtrip_json():
    outline = Outline(
        title="How to Build a Blog",
        brief="A guide for beginners",
        tone_guidance="Friendly and approachable",
        sections=[
            Section(title="Introduction", key_points=["Hook"]),
            Section(title="Getting Started", key_points=["Setup", "Tools"]),
        ],
    )
    restored = Outline.model_validate_json(outline.model_dump_json())
    assert restored == outline


def test_outline_sections_ordered():
    sections = [
        Section(title=f"Section {i}", key_points=[f"Point {i}"])
        for i in range(5)
    ]
    outline = Outline(
        title="Test",
        brief="brief",
        tone_guidance="neutral",
        sections=sections,
    )
    assert [s.title for s in outline.sections] == [f"Section {i}" for i in range(5)]
