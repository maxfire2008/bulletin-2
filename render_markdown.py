import regex
import markdown
import bleach


def check_text(match: regex.Match, visibilities: list[str]):
    text = regex.search("(?<=(<!--[^\/]+?-->\n?)).*(?=(\n?<!--\/-->))",
                        match.group(), flags=regex.DOTALL).group().strip("\n")
    visibility = regex.findall("(?<=(<!--[^\/]+?-->)).*(?=(<!--\/-->))",
                  match.group(), flags=regex.DOTALL)[0][0][4:-3]
    # print(repr(text))
    # text = search_result
    # if True:
    if (visibility.startswith("!") and visibility[1:] not in visibilities) or visibility in visibilities:
        return filter_visibility(text, visibilities)
    return ""


def filter_visibility(text: str, visibilities=["public"]):
    return regex.sub(
        "\n?<!--[^\/]+?-->(?:(?!<!--[^\/]+?-->|<!--\/-->).|(?R))*<!--\/-->",
        lambda a: check_text(a, visibilities=visibilities),
        text,
        flags=regex.DOTALL
    )


def render_markdown(text: str, visibility: str = "public"):
    text = filter_visibility(text, visibility)
    rendered_markdown = markdown.markdown(
        text,
        extensions=['tables']
    )

    return bleach.clean(
        rendered_markdown,
        tags=[
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "strong",
            "em",
            "blockquote",
            "ul",
            "ol",
            "li",
            "code",
            "a",
            "img",
        ],
        attributes={
            "*": ["class"],
            "a": ["href", "title"],
            "img": ["src", "alt", "title"],
        }
    )


if __name__ == "__main__":
    x = """Concrete is made up of 
<!--internal-->
<!--test.user@example.com-->Tim and Joe<!--/-->
<!--!test.user@example.com-->Potato heads<!--/-->
<!--/-->
<!--public-->
many *different* students
<!--/-->"""
    print(filter_visibility(x,visibilities=["internal"]))
