import re
import markdown
import bleach


def filter_visibility(text, visibility="public"):
    if visibility != "internal":
        text = re.sub("<!--internal-->(?s:.)*?<!--\/internal-->\n?", "", text)
    if visibility != "public":
        text = re.sub("<!--public-->(?s:.)*?<!--\/public-->\n?", "", text)
    text = re.sub("<!--/?internal-->\n?", "", text)
    text = re.sub("<!--/?public-->\n?", "", text)
    return text


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
