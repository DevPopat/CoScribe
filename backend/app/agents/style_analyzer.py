"""
Style analyzer agent — learns tone and writing preferences from user samples.

Makes a single call to claude-sonnet-4-6 and returns a concise style
description for use by the synthesizer.
"""

import anthropic

client = anthropic.Anthropic()


def analyze_style(writing_samples: list[str]) -> str:
    """
    Analyze writing samples and produce a tone and style description.

    :param writing_samples: Example texts provided by the user.
    :returns: A concise description of the user's writing style and tone.
    """
    if writing_samples:
        samples_text = "\n\n---\n\n".join(writing_samples)
        prompt = (
            f"Analyze the writing style in the following samples and describe "
            f"the author's tone, voice, and stylistic preferences in 2-3 sentences.\n\n"
            f"{samples_text}"
        )
    else:
        prompt = (
            "No writing samples were provided. Suggest a clear, engaging, "
            "and accessible default writing style suitable for a blog post."
        )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
