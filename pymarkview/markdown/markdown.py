import html
import re
from collections import OrderedDict


class Markdown:

    class RuleSetContainer:

        def __init__(self):
            self.rules = OrderedDict()

        def __call__(self):
            return self.rules.items()

        def add_rule(self, rule, repl):
            key = re.compile(rule)
            self.rules[key] = repl

    def __init__(self):
        self.rules_cont = Markdown.RuleSetContainer()
        self.rules_cont.add_rule(r"(?m)^ {0,3}(#+)\s(.*)", self._html_header)
        self.rules_cont.add_rule(r"([^\n]+)\n(\={3,}|\-{3,})", self._html_header_alt)
        self.rules_cont.add_rule(r"\n\s{0,3}(\*{3,}|\_{3,}|\-{3,})\n", "<hr>")
        self.rules_cont.add_rule(r"\[\!\[(.*?)\]\((.*?)\)\]\((.*?)\)", r"<a href='\3'><img src='\2' alt='\1'/></a>")
        self.rules_cont.add_rule(r"\!\[([^\[]+)\]\(([^\)]+)\)", r"<img src='\2' alt='\1'>")
        self.rules_cont.add_rule(r"\[([^\[]+)\]\(([^\)]+)\)", r"<a href='\2'>\1</a>")
        self.rules_cont.add_rule(r"(\*\*|__)(.*?)\1", r"<strong>\2</strong>")
        self.rules_cont.add_rule(r"(\*|_)(.*?)\1", r"<em>\2</em>")
        self.rules_cont.add_rule(r"\n`{3}([\S]+)?\n([\s\S]+)\n`{3}", self._html_pre)
        # self.rules_cont.add_rule(r"(?m)^((?:(?:[ ]{4}|\t).*(\n|$))+)", r"<pre>\1</pre>")
        self.rules_cont.add_rule(r"\`(.*?)\`", self._html_code)
        self.rules_cont.add_rule(r"(?sm)(^(?:[*+-]|\d+\.)\s(.*?)(?:\n{2,}))", self._html_list)
        self.rules_cont.add_rule(r"(?s)\n\>\s(.*?)(?:$|\n{2,})", self._html_blockquote)
        self.rules_cont.add_rule(r"\<(http.*?)\>", r"<a href=\1>\1</a>")

        self.rules_cont.add_rule(r"(?s)(.*?[^\:\-\,])(?:$|\n{2,})", self._html_parag)

    def parse(self, text):
        text = "\n{}\n\n".format(text)

        for rule, repl in self.rules_cont():
            text = re.sub(rule, repl, text)

        return text

    def _html_header(self, match_obj):
        level = min(match_obj.group(1).count('#'), 6)
        text = match_obj.group(2)
        return "<h{level}>{text}</h{level}>".format(level=level, text=text)

    def _html_header_alt(self, match_obj):
        level = 1 if match_obj.group(2)[0] == "=" else 2
        text = match_obj.group(1)
        return "<h{level} class='alt'>{text}</h{level}>".format(level=level, text=text)

    def _html_code(self, match_obj):
        text = html.escape(match_obj.group(1))

        return "<code>{text}</code>".format(text=text)

    def _html_pre(self, match_obj):
        lang = match_obj.group(1)
        text = html.escape(match_obj.group(2))

        return "<pre lang='{lang}'>{text}</pre>".format(lang=lang, text=text)

    def _html_list(self, match_obj):
        parents = (
            "<ol>", "</ol>") if match_obj.group(1)[0].isdigit() else ("<ul>", "</ul>")
        text = match_obj.group(2)
        lines = text.split("\n")

        res = parents[0]
        res += "<li>{text}</li>".format(text=lines[0].strip())

        for line in lines[1:]:
            res += "<li>{text}</li>".format(
                text=line.strip().partition(" ")[2])

        res += parents[1]
        return res

    def _html_parag(self, match_obj):
        text = match_obj.group(1)

        starts_with_tag = re.compile(r"^<\/?(li|h|p|block|img|hr|ul|ol|pre)")

        if starts_with_tag.match(text):
            return "\n{text}\n".format(text=text)
        else:
            return "\n<p>{text}</p>\n".format(text=text)

    def _html_blockquote(self, match_obj):
        text = match_obj.group(1).replace(">", "<br>")

        return "\n<blockquote>{text}</blockquote>".format(text=text)
