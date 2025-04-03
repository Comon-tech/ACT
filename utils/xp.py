import re


# ----------------------------------------------------------------------------------------------------
# * Experience
# ----------------------------------------------------------------------------------------------------
class Experience:
    """Utility interface for chat effort rewarding with anti-spam/exploit."""

    # --- General ---

    # Base XP for any message contribution (text, attachment, sticker, etc.)
    XP_PER_MESSAGE_BASE: int = 1

    # XP per "valid" word (meeting criteria below)
    XP_PER_WORD: float = 0.5

    # Maximum number of words to count for XP (prevents wall-of-text exploit)
    XP_WORD_COUNT_CAP: int = 100

    # XP per attachment (image, file, etc.)
    XP_PER_ATTACHMENT: int = 3

    # XP per embed (link previews, bot embeds)
    XP_PER_EMBED: int = 1  # Usually less valuable than attachments

    # XP per sticker item
    XP_PER_STICKER: int = 1  # Stickers often require deliberate selection

    # --- Anti-Spam/Exploit ---

    # Minimum length for a word to be counted for XP
    MIN_WORD_LENGTH: int = 3

    # Character Variety Threshold (ratio of unique alphanumeric chars to total alphanumeric chars)
    # Lower values indicate spam like "aaaaaaaaa" or "hahahahahaha"
    LOW_VARIETY_THRESHOLD: float = 0.15

    # Penalty multiplier applied to word XP if LOW_VARIETY_THRESHOLD is met
    LOW_VARIETY_PENALTY_MULTIPLIER: float = 0.1

    # Unique Word Ratio Threshold (ratio of unique valid words to total valid words)
    # Lower values indicate repetition like "spam spam spam spam"
    LOW_UNIQUE_WORD_RATIO_THRESHOLD: float = 0.3

    # Penalty multiplier applied to word XP if LOW_UNIQUE_WORD_RATIO_THRESHOLD is met
    LOW_UNIQUE_WORD_PENALTY_MULTIPLIER: float = 0.25

    # Maximum consecutive identical characters allowed in the original content
    MAX_CONSECUTIVE_CHARS: int = 6

    # Penalty multiplier applied to word XP if MAX_CONSECUTIVE_CHARS is exceeded
    CONSECUTIVE_CHARS_PENALTY_MULTIPLIER: float = 0.1

    @classmethod
    def _clean_message_content(cls, content: str) -> str:
        """
        Remove URLs, common markdown/formatting, mentions, custom emojis, excessive punctuation,
        and normalize whitespace to prepare text for word counting and analysis.

        Args:
            content: The raw message content string.

        Returns:
            A cleaned string suitable for word analysis.
        """
        # Lowercase for consistent processing
        text = content.lower()

        # Remove URLs first
        text = re.sub(r"https?://\S+", " ", text)

        # Remove common markdown/formatting (code blocks, bold, italics, etc.)
        # Note: This is a best-effort removal for common patterns.
        text = re.sub(
            r"```.*?```", " ", text, flags=re.DOTALL
        )  # Multi-line code blocks
        text = re.sub(r"`.*?`", " ", text)  # Inline code
        text = re.sub(r"(\*\*|__|\*|_|~~|\|\||>)\s*", " ", text)  # Formatting markers

        # Remove platform-specific elements (mentions, custom emojis)
        # These regex are common patterns but might need adjustment for other platforms
        text = re.sub(
            r"<a?:\w+:\d+>", " ", text
        )  # Discord custom emojis (<:name:id> or <a:name:id>)
        text = re.sub(r"<@!?&?#?\d+>", " ", text)  # Discord mentions/roles/channels

        # Replace punctuation (except apostrophes within words) with spaces
        text = re.sub(r"[^\w\s']", " ", text)
        # Remove apostrophes that are not within words
        text = re.sub(r"(?<!\w)'|'(?!\w)", " ", text)

        # Normalize whitespace (replace multiple spaces/tabs/newlines with a single space)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @classmethod
    def calculate_reward(
        cls,
        content: str,
        attachment_count: int = 0,
        embed_count: int = 0,
        sticker_count: int = 0,
    ) -> int:
        """
        Calculate an XP reward based on message content quality and quantity, attachments, embeds, and stickers.
        Applies anti-spam/exploit measures.

        Args:
            content: The text content of the message. Can be an empty string if
                     the message only contains attachments, stickers, etc.
            attachment_count: The number of attachments associated with the message.
            embed_count: The number of embeds (e.g., link previews) with the message.
            sticker_count: The number of stickers sent with the message.

        Returns:
            The calculated integer XP reward (guaranteed to be at least 1).
        """
        xp_reward = float(cls.XP_PER_MESSAGE_BASE)  # Start with float for penalties
        word_xp = 0.0
        original_content = content  # Keep original for consecutive char check

        # --- 1. Analyze Content for Words ---
        # Only process content if it actually exists
        if content and content.strip():
            cleaned_content = cls._clean_message_content(content)
            if cleaned_content:  # Ensure cleaning didn't remove everything
                # \b ensures whole words, \w+ matches alphanumeric sequences
                all_words = re.findall(r"\b\w+\b", cleaned_content)

                # Filter words by minimum length
                valid_words = [
                    word for word in all_words if len(word) >= cls.MIN_WORD_LENGTH
                ]
                valid_word_count = len(valid_words)

                # Apply word count cap *before* calculating XP for words
                capped_word_count = (
                    min(valid_word_count, cls.XP_WORD_COUNT_CAP)
                    if cls.XP_WORD_COUNT_CAP > 0
                    else valid_word_count
                )

                # Initial word XP calculation
                if capped_word_count > 0:
                    word_xp = capped_word_count * cls.XP_PER_WORD

                    # --- 2. Apply Penalties to Word XP based on content quality ---

                    # Penalty 1: Low Character Variety
                    if (
                        cls.LOW_VARIETY_THRESHOLD > 0 and len(cleaned_content) > 10
                    ):  # Check on cleaned content
                        alnum_chars = [c for c in cleaned_content if c.isalnum()]
                        total_alnum_chars = len(alnum_chars)
                        if total_alnum_chars > 0:
                            unique_alnum_chars = len(set(alnum_chars))
                            variety_ratio = unique_alnum_chars / total_alnum_chars
                            if variety_ratio < cls.LOW_VARIETY_THRESHOLD:
                                # print(f"Applying low variety penalty ({variety_ratio:.2f} < {cls.LOW_VARIETY_THRESHOLD})") # Debug
                                word_xp *= cls.LOW_VARIETY_PENALTY_MULTIPLIER

                    # Penalty 2: Low Unique Word Ratio
                    if (
                        word_xp > 0
                        and cls.LOW_UNIQUE_WORD_RATIO_THRESHOLD > 0
                        and valid_word_count > 5
                    ):  # Need enough words
                        unique_valid_words = len(set(valid_words))
                        unique_ratio = unique_valid_words / valid_word_count
                        if unique_ratio < cls.LOW_UNIQUE_WORD_RATIO_THRESHOLD:
                            # print(f"Applying low unique word penalty ({unique_ratio:.2f} < {cls.LOW_UNIQUE_WORD_RATIO_THRESHOLD})") # Debug
                            word_xp *= cls.LOW_UNIQUE_WORD_PENALTY_MULTIPLIER

                    # Penalty 3: Excessive Consecutive Identical Characters
                    # Check original content for sequences like "ggggggg"
                    if word_xp > 0 and cls.MAX_CONSECUTIVE_CHARS > 0:
                        # Find any character repeated MAX_CONSECUTIVE_CHARS or more times
                        if matches := re.findall(
                            r"(.)\1{" + str(cls.MAX_CONSECUTIVE_CHARS - 1) + r",}",
                            original_content,
                        ):
                            # print(f"Applying consecutive char penalty (found sequences like {matches[0]*cls.MAX_CONSECUTIVE_CHARS}...)") # Debug
                            word_xp *= cls.CONSECUTIVE_CHARS_PENALTY_MULTIPLIER

        # Add potentially penalized word XP to total
        xp_reward += word_xp

        # --- 3. Add XP for Attachments, Embeds, and Stickers ---
        xp_reward += attachment_count * cls.XP_PER_ATTACHMENT
        xp_reward += embed_count * cls.XP_PER_EMBED
        xp_reward += sticker_count * cls.XP_PER_STICKER  # Add sticker XP

        # --- 4. Finalize ---
        # Ensure at least 1 XP, even for penalized or content-less messages
        # (e.g., a message with only a sticker should get base + sticker XP)
        final_xp = max(1, int(round(xp_reward)))

        # Optional: Add detailed debug logging if needed
        # print(f"Content='{content[:30]}' Attach={attachment_count} Embed={embed_count} Sticker={sticker_count} | Clean='{cleaned_content[:30]}' Words={valid_word_count}({capped_word_count}) WordXP={word_xp:.2f} | FinalXP={final_xp}")

        return final_xp
