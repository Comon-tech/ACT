from discord import Color, Embed


class EmbedX:
    @staticmethod
    def info(title: str = "", description: str = "") -> Embed:
        return Embed(
            title=f":information_source: {title}",
            description=description,
            color=Color.blue(),
        )

    @staticmethod
    def success(title: str = "", description: str = "") -> Embed:
        return Embed(
            title=f":white_check_mark: {title}",
            description=description,
            color=Color.green(),
        )

    @staticmethod
    def warning(title: str = "", description: str = "") -> Embed:
        return Embed(
            title=f":warning: {title}", description=description, color=Color.yellow()
        )

    @staticmethod
    def error(title: str = "", description: str = "") -> Embed:
        return Embed(
            title=f":no_entry: {title}", description=description, color=Color.red()
        )
