def preprocess_transcript(text: str) -> str:
    """
    Convert dialogue-format transcript into continuous readable text.

    Removes excessive blank lines and unnecessary line breaks while
    preserving speaker names. The original transcript file on disk
    is never modified.

    Example:
        Input:
            John:
            Hello everyone.

            Alice:
            Let's begin.

        Output:
            "John: Hello everyone. Alice: Let's begin."
    """
    lines = text.strip().split("\n")
    cleaned = [line.strip() for line in lines if line.strip()]
    return " ".join(cleaned)
