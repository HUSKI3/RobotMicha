from html.parser import HTMLParser
import inspect
import mimetypes
import os
import re

from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel

def Proc(cls):
    for name, func in cls.__dict__.items():
        if hasattr(func, '_rule_instance'):
            if func.__doc__:
                cls.rules[func.__doc__.strip('?')] = func
            else:
                cls.rules[name] = func

        elif hasattr(func, '_data_rule_instance'):
            if func.__doc__:
                cls.data_rules[func.__doc__.strip('?')] = func
            else:
                cls.data_rules[name] = func
        
        elif hasattr(func, '_ending_rule_instance'):
            if func.__doc__:
                cls.ending_rules[func.__doc__.strip('?')] = func
            else:
                cls.ending_rules[name] = func
        
        elif hasattr(func, '_suggestion_instance'):
            if func.__doc__:
                cls.suggestions[func.__doc__.strip('?')] = func
            else:
                cls.suggestions[name] = func
    return cls

console = Console()

@Proc
class Parser(HTMLParser):
    rules = {}
    suggestions = {}
    data_rules = {}
    ending_rules = {}

    def rule(function, **kwargs):
        function._rule_instance = {
            "name"  : function.__name__
        } 
        return function
    
    def suggestion(function, **kwargs):
        function._suggestion_instance = {
            "name"  : function.__name__
        } 
        return function
        
    def data_rule(function, **kwargs):
        function._data_rule_instance = {
            "name"  : function.__name__
        } 
        return function

    def ending_rule(function, **kwargs):
        function._ending_rule_instance = {
            "name"  : function.__name__
        } 
        return function


    @rule
    def disalow_inline_style(self, tag, attr):
        if attr:
            if 'style' in attr[0]:
                self.rules_broken.append(
                    {
                        "name": inspect.stack()[0][3].upper(),
                        "loc": self.getpos()[0],
                        "fix": f"In tag '{tag}' Remove '{attr[0][0]}' attribute"
                    }
                )


    @rule
    def disalow_embed_style(self, tag, attr):
        if tag == 'style':
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Move contents from '{tag}' to a 'css/style.css' file"
                }
            )
        
    @data_rule
    def invalid_entity(self, data):
        # This will actually only resolve if there are invalid entities, 
        # since HTML Parser will already resolve the valid ones itself
        entities = re.findall("&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-fA-F]{1,6});", data)
        if entities:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Invalid entities {entities}"
                }
            )

    @rule
    def css_source_css(self, tag, attr):
        if tag == 'link':
            attrs = dict(attr)
            if ('href' in attrs) and not (re.findall('css\/',attrs["href"])):
                self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"CSS File linking should be done from a 'css/' folder. Example: 'css/style.css'"
                }
            )
    
    @rule
    def css_valid_src(self, tag, attr):
        if tag == 'link':
            attrs = dict(attr)
            if ('href' in attrs):
                if not os.path.exists(os.path.join('web',attrs['href'])):
                    self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Image at '{attrs['href']}' does not exist"
                }
            )
    
    @rule
    def img_source_img(self, tag, attr):
        if tag == 'img':
            attrs = dict(attr)
            if ('src' in attrs) and not (re.findall('img\/',attrs["src"])):
                self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Image loading should be done from an 'img/' folder. Example: 'img/example.png'"
                }
            )
    
    @rule
    def img_alt_attr(self, tag, attr):
        if tag == 'img':
            attrs = dict(attr)
            if not ('alt' in attrs):
                self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Images should have an 'alt' attribute. Example: [code]<img src=\"...\" alt=\"example\" title=\"...\"> [/code]"
                }
            )
    
    @rule
    def img_title_attr(self, tag, attr):
        if tag == 'img':
            attrs = dict(attr)
            if not ('alt' in attrs):
                self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Images should have a 'title' attribute. Example: [code]<img src=\"...\" alt=\"...\" title=\"example\"> [/code]"
                }
            )

    @suggestion 
    def top_level_statement_article(self, tag, attr):
        if self.prev_tag == 'article' and tag not in ['h2', 'h3', 'h4', 'h5', 'h6']:
            attrs = dict(attr)
            if not ('alt' in attrs):
                self.suggestions_available.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0]-1,
                    "endloc": self.getpos()[0],
                    "fix": f"Article lacks heading. Consider using h2-h6 elements to add identifying headings to all articles"
                }
            )

    @rule
    def video_size_attr(self, tag, attr):
        if tag == 'video':
            attrs = dict(attr)
            if (('width' in attrs) and ((attrs['width'].isdigit()) or (attrs['width'][-2:] == 'px'))) \
                or \
                (('height' in attrs) and (attrs['height'].isdigit() or (attrs['height'][-2:] == 'px'))):
                self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Video size should not be set in pixels."
                }
            )
    
    @rule
    def fig_img_attr(self, tag, attr):
        if self.prev_tag != 'figure' and tag == 'img':
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Images should be contained in a '<figure>' element. Example: [code]<figure> <img> <figcaption></figcaption> </figure>[/code]"
                }
            )
    
    @rule
    def fig_img_attr(self, tag, attr):
        if self.prev_tag == 'img' and tag != 'figcaption':
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0]-1,
                    "fix": f"Figure elements should contain a '<figcaption>' element. Example: [code]<figure> <img> <figcaption></figcaption> </figure>[/code]"
                }
            )
    
    @rule
    def img_valid_src(self, tag, attr):
        if tag == 'img':
            attrs = dict(attr)
            if ('src' in attrs):
                mimetype, encoding = mimetypes.guess_type(attrs['src'])
                if not os.path.exists(os.path.join('web',attrs['src'])):
                    self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Image at '{attrs['src']}' does not exist"
                }
            )
    
    @rule
    def meta_author(self, tag, attr):
        if tag == 'meta':
            attrs = dict(attr)
            if 'name' in attrs:
                name = attrs['name']
                self.meta_names.append(name)
    
    @ending_rule
    def meta_end(self):
        expect = [
                'author',
                'keywords',
                'description'
            ]
        expect.sort()
        self.meta_names.sort()
        if (expect != self.meta_names):
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a full set of meta attributes, only '{', '.join(self.meta_names)}'. Need: 'author, keywords, description'"
                }
            )

    @ending_rule
    def page_title(self):
        if self.check_objects.get('title') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<title>' tag in the header"
                }
            )
    
    @ending_rule
    def page_head(self):
        if self.check_objects.get('head') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<head>' tag"
                }
            )

    @ending_rule
    def page_body(self):
        if self.check_objects.get('body') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<body>' tag"
                }
            )
    
    @ending_rule
    def page_h1(self):
        if self.check_objects.get('h1') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<h1>' tag"
                }
            )
    
    @ending_rule
    def page_h2(self):
        if self.check_objects.get('h2') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<h2>' tag"
                }
            )
    
    @ending_rule
    def page_p(self):
        if self.check_objects.get('p') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<p>' tag"
                }
            )
    
    @ending_rule
    def page_strong(self):
        if self.check_objects.get('strong') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<strong>' tag"
                }
            )
    
    @ending_rule
    def page_link(self):
        if self.check_objects.get('link') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<link>' tag, this is used to include 'css'. Example: [code]<link rel=\"stylesheet\" href=\"css/style.css\">[/code]"
                }
            )
    
    @ending_rule
    def page_section(self):
        if self.check_objects.get('section') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<section>' tag"
                }
            )
    
    @ending_rule
    def page_article(self):
        if self.check_objects.get('article') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<article>' tag"
                }
            )
    
    @ending_rule
    def page_aside(self):
        if self.check_objects.get('aside') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<aside>' tag"
                }
            )
    
    @ending_rule
    def page_nav(self):
        if self.check_objects.get('nav') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<nav>' tag"
                }
            )
    
    @ending_rule
    def page_em(self):
        if self.check_objects.get('em') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<em>' tag"
                }
            )
    
    @ending_rule
    def page_html(self):
        if self.check_objects.get('html') == None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage does not contain a '<html>' tag"
                }
            )
    
    @ending_rule
    def page_div(self):
        if self.check_objects.get('div') != None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage has a '<div>' tag. Divs are not allowed"
                }
            )
    
    @ending_rule
    def page_hr(self):
        if self.check_objects.get('hr') != None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage has a '<hr>' tag. Hr tags are not allowed"
                }
            )
    
    @ending_rule
    def page_br(self):
        if self.check_objects.get('br') != None:
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage has a '<br>' tag. Br tags are not allowed"
                }
            )
    
    @ending_rule
    def page_playback(self):
        if self.check_objects.get('video') == None:
            syntax = Syntax('''\
<video>
    <source src="movie.mp4" type="video/mp4">
    <source src="movie.ogg" type="video/ogg">
    Your browser does not support the video tag.
</video>''', 'HTML', padding=1)
            self.rules_broken.append(
                {
                    "name": inspect.stack()[0][3].upper(),
                    "loc": self.getpos()[0],
                    "fix": f"Webpage has no '<video>' tag",
                    "fix-code": syntax
                }
            )



    def __init__(self, *, convert_charrefs: bool = ...) -> None:
        self.dom = None
        self.rules_broken = []
        self.suggestions_available = []
        self.check_objects = {}
        self.meta_names = []
        super().__init__(convert_charrefs=convert_charrefs)

        self.flags = {
            #'DISALLOW_INLINE_STYLE': False,
            #'DISALLOW_EMBED_STYLE': False,
            #'VALID_ENTITY': False,
            #'CSS_SOURCE_CSS': False,
            #'IMG_SOURCE_IMG': False,
            #'IMG_ALT_ATTR': False,
            #'IMG_TITLE_ATTR': False,
            #'FIG_IMG_ATTR': False,
            #'IMG_VALID_SRC': False,
            #'HTML_DOC_TAG': False,
            #'PAGE_TITLE': False,
            #'HEAD_TAG': False,
            #'BODY_TAG': False,
            #'H1_PRESENT': False,
            #'H2_PRESENT': False,
            #'P_PRESENT': False,
            #'STRONG_PRESENT': False,
            #'DISALLOW_DIV': False,
            #'FIG_CAPTION_PRESENT': False,
            #'LINK_PRESENT': False,
            #'SECTION_PRESENT': False,
            #'ARTICLE_PRESENT': False,
            #'ASIDE_PRESENT': False,
            #'NAV_PRESENT': False,
            #'FOOTER_PRESENT': False,
            #'EM_PRESENT': False,
            #'DISALLOW_HR': False,
            #'DISALLOW_BR': False,
            #'PLAYBACK_PRESENT': False,
            # X 'PLAYBACK_OGG_MP4_PRESENT': False,
            #'METADATA_HAS_AUTHOR': False,
            #'METADATA_HAS_DESC': False,
            #'METADATA_HAS_KEYWORDS': False,
            'FORM_PRESENT': False,
            'FORM_EMAIL': False,
            'FORM_SUBMIT': False,
            'COPY_PRESENT': False,
            'ANCHOR_PRESENT': False,
            'ORDERED_LIST_PRESENT': False,
            'UNORDERED_LIST_PRESENT': False,
            # Basics but oddly specific
            'FONT_NOTABLE': False,
            'FONT_ARIAL': False,
            'FONT_HELVETICA': False,
            'FONT_SANS_SERIF': False,
            'PAN_CMYK_COLOR': False,
            'RELATIVE_UNITS': False,
            'ANCHOR_ELEMENT': False,
            'COPYRIGHT_PRESENT': False,
            # IDK HOW TO IMPLEMENT
            'RESPONSIVE': False
        }

    def feed(self, data: str, dom) -> None:
        self.dom = dom
        self.data = data
        self.prev_tag = 'html'
        # Validate doctype here
        if '<!DOCTYPE html>' not in data:
            self.rules_broken.append(
                {
                    "name": "HTML_DOC_TAG",
                    "loc": 1,
                    "fix": f"Webpage should contain a doctag Example: [code]<!DOCTYPE html>[/code]"
                }
            )
        super().feed(data)
        
        for rule in self.ending_rules:
            self.ending_rules[rule](self)

    def log(self, tag, attrs=[]):
        pass
        
    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.log(tag, attrs)

        for rule in self.rules:
            self.rules[rule](self, tag, attrs)
        for s in self.suggestions:
            self.suggestions[s](self, tag, attrs)
        self.prev_tag = tag
        self.check_objects[tag] = True
    
    def handle_data(self, data: str) -> None:
        if data.strip():
            for rule in self.data_rules:
                self.data_rules[rule](self, data)

    def handle_endtag(self, tag: str) -> None:
        #return super().handle_endtag(tag)
        #elf.log(tag)
        pass

    def print_suggestions(self):
        for sug in self.suggestions_available:
            console.print(f"SUGGESTION: [bold magenta]{sug['name']}[/bold magenta]!")
            syntax = Syntax(
                self.data, 
                "HTML", 
                padding=1, 
                line_numbers=True,
                line_range= [sug['loc'], [sug['endloc'] if 'endloc' in sug else sug['loc']][0]]
            )
            console.print(syntax)
            console.print(f"[bold green]Suggested fix: [/bold green] {sug['fix']}")
            if 'fix-code' in sug:
                console.print("[bold green]Suggested code:[/bold green]")
                console.print(sug['fix-code'])
            print('\n')

    def print_broken(self):
        failed = []
        for rule in self.rules_broken:
            console.print(f"RULE BROKEN: [bold magenta]{rule['name']}[/bold magenta]!")
            syntax = Syntax(
                self.data, 
                "HTML", 
                padding=1, 
                line_numbers=True,
                line_range= [rule['loc'], [rule['endloc'] if 'endloc' in rule else rule['loc']][0]]
            )
            console.print(syntax)
            console.print(f"[bold green]Suggested fix: [/bold green] {rule['fix']}")
            if 'fix-code' in rule:
                console.print("[bold green]Suggested code:[/bold green]")
                console.print(rule['fix-code'])
            print('\n')
            failed.append(f"[red]{rule['name']}[/red] \t-> line {rule['loc']}")
        
        failed = '\n'.join(failed)
        failed += f"{len(self.suggestions_available)} suggestions available"
        console.print(Panel(f"[red bold]Micha: Did you even come to the lecture?[/red bold]"+'\n'+f"{failed}", title="Oh no..."))


class Website:
    def __init__(
        self,
        source: str
    ) -> None:
        self.source = source
        self.parser = Parser()
        self.DOM = {}
    
    def parse(self):
        self.parser.feed(
            open(self.source, "rt").read(),
            self.DOM
        )
        if self.parser.rules_broken:
            self.parser.print_broken()
        else:
            console.print(Panel("[green]All checks passed![/green]\n"+f"{len(self.parser.suggestions_available)} suggestions available", title="Micha: *cough* Hard *cough*"))
        
        if len(self.parser.suggestions_available) > 0:
            self.parser.print_suggestions()