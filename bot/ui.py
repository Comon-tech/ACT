from discord import Color, Embed


class EmbedX:
    @staticmethod
    def info(title: str = "Info", description: str = "") -> Embed:
        return Embed(
            title=f":information_source: {title}",
            description=description,
            color=Color.blue(),
        )

    @staticmethod
    def success(title: str = "Success", description: str = "") -> Embed:
        return Embed(
            title=f":white_check_mark: {title}",
            description=description,
            color=Color.green(),
        )

    @staticmethod
    def warning(title: str = "Warning", description: str = "") -> Embed:
        return Embed(
            title=f":warning: {title}", description=description, color=Color.yellow()
        )

    @staticmethod
    def error(title: str = "Error", description: str = "") -> Embed:
        return Embed(
            title=f":no_entry: {title}", description=description, color=Color.red()
        )
