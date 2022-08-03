import regex
import markdown
import bleach

import evalidate


def evaluate_visibility(visibility, visibilities):
    if visibility.startswith("$"):
        success, result = evalidate.safeeval(
            src=visibility[1:],
            context={
                "visibilities": visibilities
            },
            addnodes=['Call'],
            funcs=['int', 'min', 'max']
        )
        if success and type(result) == bool:
            return result
        return False
    elif visibility.startswith("@"):
        return visibility[1:] in visibilities
    elif visibility.startswith("!"):
        return visibility[1:] not in visibilities


def check_text(match: regex.Match, visibilities: list[str]):
    if callable(visibilities):
        get_match = visibilities
    else:
        def get_match(a): return evaluate_visibility(a, visibilities)
    text = regex.search("(?<=(<!--[^\/]+?-->\n?)).*(?=(\n?<!--\/-->))",
                        match.group(), flags=regex.DOTALL).group().strip("\n")
    visibility = regex.findall("(?<=(<!--[^\/]+?-->)).*(?=(<!--\/-->))",
                               match.group(), flags=regex.DOTALL)[0][0][4:-3]
    # print(repr(text))
    # text = search_result
    # if True:
    if get_match(visibility):
        return filter_visibility(text, visibilities)
    return ""


def filter_visibility(text: str, visibilities: list[str]):
    return regex.sub(
        "\n?<!--[^\/]+?-->(?:(?!<!--[^\/]+?-->|<!--\/-->).|(?R))*<!--\/-->",
        lambda a: check_text(a, visibilities=visibilities),
        text,
        flags=regex.DOTALL
    )


def render_markdown(text: str, visibilities: list[str]):
    text = filter_visibility(text, visibilities)
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
    print(filter_visibility(x, visibilities=["internal"]))
