import air
import json
import pathlib
from typing import Any
from frontmatter import Frontmatter
from fastapi import HTTPException
import mistletoe
from functools import partial
from datetime import datetime

markdown = partial(mistletoe.markdown)


def pretty_date(date: str):
    return datetime.strptime(date, "%Y-%m-%d").strftime("%B %-d, %Y")

app = air.Air()
jinja = air.JinjaRenderer(directory="templates")

HEADER_TAG_TYPES = (air.Header,)
FOOTER_TAG_TYPES = (air.Footer,)

# TODO add theme color enumerator for muCss

def filter_header_tags(tags: tuple) -> list:
    """Given a list of tags, only list the ones that belong in header of an HTML document.

    Returns:
        List of tags that belong in the header of an HTML document.
    """
    return [t for t in tags if isinstance(t, HEADER_TAG_TYPES)]

def filter_footer_tags(tags: tuple) -> list:
    """Given a list of tags, only list the ones that belong in footer of an HTML document.

    Returns:
        List of tags that belong in the footer of an HTML document.
    """
    return [t for t in tags if isinstance(t, FOOTER_TAG_TYPES)]    

def filter_body_tags(tags: tuple) -> list:
    """Given a list of tags, only list the ones that belong in header of an HTML document.

    Returns:
        List of tags that belong in the header of an HTML document.
    """
    return [t for t in tags if not isinstance(t, HEADER_TAG_TYPES+HEADER_TAG_TYPES+FOOTER_TAG_TYPES)]


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
    body_tags = filter_body_tags(air.layouts.filter_body_tags(children))
    head_tags = air.layouts.filter_head_tags(children)
    header_tags = filter_header_tags(children)
    footer_tags = filter_footer_tags(children)

    if is_htmx:
        return air.Children(air.Main(*body_tags, class_="container"), *head_tags)

    return air.Html(
        air.Head(
            air.Link(
                rel="stylesheet",
                href=f"https://unpkg.com/@digicreon/mucss/dist/mu.{theme}.css",
            ),
            air.Link(
                rel="stylesheet",
                href="/static/style.css"
            ),
            air.Script(
                src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.6/dist/htmx.min.js",
                integrity="sha384-Akqfrbj/HpNVo8k11SXBb6TlBWmXXlYQrCSqEWmyKJe+hDm3Z/B2WVG4smwBkRVm",
                crossorigin="anonymous",
            ),
            *head_tags,
        ),    
        air.Body(
            *header_tags,    
            air.Main(*body_tags, class_="container"),
            *footer_tags,
        ),
                
        data_theme = 'dark' if force_dark_mode else ''
    )


def Header():
    return air.Header(
        air.Nav(
            air.Ul(
                air.Li(
                    air.A(air.Strong('Grimdaniel'),href='/'),
                ),
            ),
            air.Input(
                hidden=True,
                type_='checkbox',
                class_='navbar-toggle',
                id_='nav-full',
            ),
            air.Label(
                '☰',
                for_='nav-full',
                class_='navbar-burger',
            ),
            air.Ul(
                air.Li(
                    air.A('Home', href='/'),
                ),
                air.Li(
                    air.A('About', href='/about'),
                ),
                air.Li(
                    air.A('Newsletter', href=newsletter.url()),
                ),  
                air.Li(
                    air.A('Reviews', href=reviews.url()),
                ),                                  
                class_='navbar-menu',
            ),
            class_='container',
        ),
        class_='bg-primary sticky-top',
    )  


@app.page
def index(request: air.Request):
    return MarkdownPage('index')


redirect_items = json.loads(pathlib.Path("redirects.json").read_text())


def Footer(title: str, slug: str = ''):
    dirs = [x for x in slug.split('/')[:-1]]
    return air.Footer(
        air.Nav(
            air.Ul(
                air.Li(
                    air.A('Home', href='/'),
                ),
                *[air.Li(air.A(x, href=f'/{x}')) for x in dirs],
                air.Li(title, aria_current='page'),
                class_='breadcrumb',
            ),
            aria_label='Breadcrumb',
        ),   
        air.P(air.Small(air.Raw("&copy;"), "2026 Daniel Roy Greenfeld")),     
        class_='container'
    )


    

def MarkdownPage(slug: str):
    """Renders a non-sequential markdown file"""
    try:
        content = Frontmatter.read_file(f"pages/{slug}.md")
    except FileNotFoundError:
        raise HTTPException(status_code=404)
    date = content["attributes"].get("date", "")
    title = content["attributes"].get("title", slug)
    if title == 'index':
        title = 'Grimdaniel'
    social_title = content["attributes"].get("social_title", title)
    description = content["attributes"].get("description", '')
    social_description = content["attributes"].get("social_description", description)
    image = content["attributes"].get("image", 'https://grimdaniel.com/static/images/the-curse.webp')
    if not image.startswith('https://'):
        image = f'https://grimdaniel.com{image}'
    twitter_image = content["attributes"].get("twitter_image", image)
    if not twitter_image.startswith('https://'):
        twitter_image = f'https://grimdaniel.com{twitter_image}'
    author = content["attributes"].get("author", "")
    text = markdown(content["body"])
    breadcrumbs = content["attributes"].get("breadcrumbs", [])
    return mucss(
        air.Meta(charset='UTF-8'),
        air.Meta(name='viewport', content='width=device-width, initial-scale=1.0'),
        air.Meta(name='description', content=social_description),
        air.Meta(property='og:title', content=social_title),
        air.Meta(property='og:description', content=social_description),
        air.Meta(property='og:image', content=image),
        air.Meta(property='og:type', content='website'),
        air.Meta(property='og:url', content=f'https://grimdaniel.com/{slug}'),
        air.Meta(name="twitter:image", content=twitter_image),
        air.Meta(name='twitter:card', content='summary_large_image'),   
        air.Meta(name='twitter:site', content="@pydanny"),
        air.Meta(name='twitter:title', content=social_title),
        air.Meta(name='twitter:description', content=social_description),     
        air.Title(social_title),
        Header(),
        air.Section(
            air.H1(title) if title != 'Grimdaniel' else '',
            air.P(
                f'by {author}',
            ) if author else '',
            air.P(description) if description else '',
            air.Br() if description else '',
            air.Div(air.Raw(text)),
        ),
        Footer(title, slug),
        title=title,
        description=content["attributes"].get("description", ""),
        theme='red',
        force_dark_mode=True
    )

@app.page
def newsletter():
    title = 'The Not Dead Yet Newsletter'
    newsletters = sorted(
        [x for x in pathlib.Path('pages/newsletter/').glob('*.md')
         if (datetime.now() - datetime.strptime(x.stem, "%Y-%m-%d")).days >= 8 or x.stem=='2024-04-10'],
        reverse=True
    )

    return mucss(        
        Header(),
        air.Title(title),
        air.H1(title),
        air.Div(air.Raw(markdown("""
My newsletter on grimdark fiction is sent out every week on Friday. Previous newsletters are listed here within two weeks after mailout.
Signup and you'll receive FREE access to "[The Curse](/the-curse)", prelude to "[Everyone Dies](/everyone-dies)." Unsubscribe anytime.

<a href="/list-signup" class="btn btn-primary" target="_blank">Signup to the Not Dead Yet Newsletter</a>"""))),
        air.H2("Past editions of the newsletter"),
        air.Ol(
            *[air.Li(air.A(pretty_date(x.stem), href=page_or_redirect.url(slug=f'newsletter/{x.stem}'))) for x in newsletters],
            reversed=True
        ),
        Footer(title),
        theme='red',
        force_dark_mode=True
    )

@app.page
def reviews():
    title = "Book reviews of other author's works"
    reviews =  pathlib.Path('pages/reviews/').glob('*.md')
    return mucss(        
        Header(),
        air.Title(title),
        air.H1(title),
        air.Ol(
            *[air.Li(air.A(Frontmatter.read_file(x)['attributes']['title'].replace('Review: ', ''), href=page_or_redirect.url(slug=f'reviews/{x.stem}'))) for x in reviews]
        ),
        Footer(title),
        theme='red',
        force_dark_mode=True
    )

@app.page
def signed_up(request: air.Request):
        return jinja(
        request,
        name="signed_up.html"
    )

@app.page
def redirects():
    return mucss(
        Header(),
        air.Ol(
            *[air.Li(x,": " , air.A(redirect_items[x], href=redirect_items[x], target='_blank')) for x in redirect_items]
        ),
        Footer('Redirects'),
        theme='red',
        force_dark_mode=True
    )        


@app.get("/robots.txt")
def robots_txt(request: air.Request):
    return air.responses.PlainTextResponse(Path('templates/robots.txt').read_text())

@app.get("/{slug:path}")
async def page_or_redirect(slug: str):
    redirects_url = redirect_items.get(slug, None)
    if redirects_url is not None:
        return air.RedirectResponse(redirects_url)
    try:
        return MarkdownPage(slug)
    except TypeError:
        raise HTTPException(status_code=404)