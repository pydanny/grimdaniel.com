import air
import json
import pathlib
from typing import Any
from frontmatter import Frontmatter
from fastapi import HTTPException
import mistletoe
from functools import partial

markdown = partial(mistletoe.markdown)

app = air.Air()
jinja = air.JinjaRenderer(directory="templates")

# TODO add theme color enumerator for muCss


def mucss(*children: Any, theme:str='red', force_dark_mode:bool=False, is_htmx: bool = False, **kwargs) -> air.Html | air.Children:
    """Renders the basic layout with MuCSS and HTMX for quick prototyping.

    1. At the top level HTML head tags are put in the `<head>` tag
    2. Otherwise everything is put in the `<body>`
    3. If `is_htmx` is True, then the layout isn't included. This is to support the `hx_boost`
        feature of HTMX

    Note: `MuCSS` is a quick prototyping tool. It isn't designed to be extensible.
        Rather the `MuCSS` layout function makes it easy to roll out quick demonstrations and proofs-of-concept.
        For more advanced layouts like Eidos or a full-fledged MuCSS implementation,
        you'll have to create your own layouts.

    Args:
        children: These typically inherit from air.Tag but can be anything
        is_htmx: Whether or not HTMX sent the request from the page

    Returns:
        HTML document with MuCSS styling or Children for HTMX partial responses.

    Example:

        import air

        app = air.Air()


        @app.page
        async def index(request: air.Request) -> air.Html | air.Children:
            return air.layouts.MuCSS(
                air.Title("Home"),
                air.Article(
                    air.H1("Welcome to Air"),
                    air.P(air.A("Click to go to Dashboard", href="/dashboard")),
                    hx_boost="true",
                ),
                is_htmx=request.htmx.is_hx_request,
            )


        @app.page
        async def dashboard(request: air.Request) -> air.Html | air.Children:
            return air.layouts.MuCSS(
                air.Title("Dashboard"),
                air.Article(
                    air.H1("Dashboard"),
                    air.P(air.A("Go home", href="/")),
                    hx_boost="true",
                ),
                is_htmx=request.htmx.is_hx_request,
            )


        if __name__ == "__main__":
            import uvicorn

            uvicorn.run(app, host="127.0.0.1", port=8000)
    """
    body_tags = air.layouts.filter_body_tags(children)
    head_tags = air.layouts.filter_head_tags(children)

    if is_htmx:
        return air.Children(air.Main(*body_tags, class_="container"), *head_tags)

    return air.Html(
        air.Head(
            air.Link(
                rel="stylesheet",
                href=f"https://unpkg.com/@digicreon/mucss/dist/mu.{theme}.css",
            ),
            air.Script(
                src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js",
                integrity="sha384-Akqfrbj/HpNVo8k11SXBb6TlBWmXXlYQrCSqEWmyKJe+hDm3Z/B2WVG4smwBkRVm",
                crossorigin="anonymous",
            ),
            *head_tags,
        ),
        air.Body(air.Main(*body_tags, class_="container"), class_="container"),
        data_theme = 'dark' if force_dark_mode else ''
    )


@app.page
def index(request: air.Request):
    return MarkdownPage('books')


redirects = json.loads(pathlib.Path("redirects.json").read_text())

def MarkdownPage(slug: str):
    """Renders a non-sequential markdown file"""
    try:
        content = Frontmatter.read_file(f"pages/{slug}.md")
    except FileNotFoundError:
        raise HTTPException(status_code=404)
    date = content["attributes"].get("date", "")
    title = content["attributes"].get("title", slug)
    description = content["attributes"].get("description", '')
    image = content["attributes"].get("image", 'https://grimdaniel.com/static/books/everyone-dies.webp')
    author = content["attributes"].get("author", "")
    return mucss(
        air.Meta(charset='UTF-8'),
        air.Meta(name='viewport', content='width=device-width, initial-scale=1.0'),
        air.Meta(name='description', content=description),
        air.Meta(property='og:title', content=title),
        air.Meta(property='og:description', content=description),
        air.Meta(property='og:image', content=image),
        air.Meta(property='og:type', content='website'),
        air.Meta(property='og:url', content='https://grimdaniel.com'),
        air.Meta(name='twitter:card', content='summary_large_image'),        
        air.Title(title),
        air.Section(
            air.H1(content["attributes"].get("title", "")),
            air.P(
                f'by {author}',
            ) if author else '',
            air.Small(air.Time(date)),
            air.P(description),
            air.Br(),
            air.Div(air.Raw(markdown(content["body"]))),
        ),
        air.Nav(
            air.Ul(
                air.Li(
                    air.A('Home', href='/'),
                ),
                air.Li(title, aria_current='page'),
                class_='breadcrumb',
            ),
            aria_label='Breadcrumb',
        ),   
        title=title,
        description=content["attributes"].get("description", ""),
        theme='red',
        force_dark_mode=True
    )

@app.page
def signed_up(request: air.Request):
        return jinja(
        request,
        name="signed_up.html"
    )


@app.get("/robots.txt")
def robots_txt(request: air.Request):
    return air.responses.PlainTextResponse(Path('templates/robots.txt').read_text())

@app.get("/{slug:path}")
async def page_or_redirect1(slug: str):
    redirects_url = redirects.get(slug, None)
    if redirects_url is not None:
        return air.RedirectResponse(redirects_url)
    try:
        return MarkdownPage(slug)
    except TypeError:
        raise HTTPException(status_code=404)