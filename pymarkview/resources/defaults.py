welcome_text = '''PyMarkView
===

Overview
---

Supports **bold**, *italic* and ***bold-italic***!
Inline `code` is possible, too!

Images can be inserted using drag and drop or the corresponding MD syntax.

```
#include<stdio.h>
int main() {
    printf("Hello world!\\n");
}
```

> A famous quote!
> Multiline!

* Unordered
* foo

1. Ordered
2. bar

###### I am a tiny header!

Types of links: <https://github.com/> [GitHub](https://github.com/)

CLI usage
---

`$ pymarkview -i "input.md" -o "output.html"`
'''

stylesheet = '''<style>
body {
    font-family: sans-serif;
}

h1.alt, h2.alt {
    border-bottom: 1px solid #eee;
}

hr {
    border: 0;
    border-top: 1px solid #eee;
}

blockquote {
    margin-left: 0;
    padding-left: 10px;
    border-left: 4px solid #dfe2e5;
}

code {
    background: #f6f8fa;
    border-radius: 3px;
    padding: 2px;
}

pre {
    background: #f6f8fa;
    padding: 16px;
    border-radius: 3px;
}

img {
  max-width: 50%;
  vertical-align: middle;
}
</style>
'''

mathjax = '''<script async type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.2/MathJax.js?config=TeX-MML-AM_CHTML"></script>'''
