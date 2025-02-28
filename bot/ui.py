from discord import Color, Embed


class EmbedX:
    STYLES = {
        "info": {"color": Color.blue(), "icon": ":information_source:"},
        "success": {"color": Color.green(), "icon": "✅"},
        "warning": {"color": Color.yellow(), "icon": "⚠️"},
        "error": {"color": Color.red(), "icon": "⛔"},
    }

    @classmethod
    def _create(
        cls,
        style_name: str,
        description: str,
        title: str | None = None,
        icon: str | None = None,
    ) -> Embed:
        """Creates a styled embed."""
        if style_name not in cls.STYLES:
            raise ValueError(f"Invalid embed style: {style_name}")
        style = cls.STYLES[style_name]
        if icon == None:
            icon = style["icon"]
        if title == None:
            title = style_name.capitalize()
        return Embed(
            title=f"{icon.strip()} {title.strip()}",  # type: ignore
            description=description.strip(),
            color=style["color"],
        )

    @classmethod
    def info(
        cls, description="", title: str | None = None, icon: str | None = None
    ) -> Embed:
        return cls._create("info", description, title, icon)

    @classmethod
    def success(
        cls, description="", title: str | None = None, icon: str | None = None
    ) -> Embed:
        return cls._create("success", description, title, icon)

    @classmethod
    def warning(
        cls, description="", title: str | None = None, icon: str | None = None
    ) -> Embed:
        return cls._create("warning", description, title, icon)

    @classmethod
    def error(
        cls, description="", title: str | None = None, icon: str | None = None
    ) -> Embed:
        return cls._create("error", description, title, icon)
