
## Markdown Examples

**Markdown Cheat Sheet and Snippets, ready to copy-paste into your documents.**

This Markdown cheat sheet provides a quick overview of all the Markdown syntax elements. It can’t cover every edge case, so if you need more information about any of these elements, refer to the reference guides for [basic syntax](https://www.markdownguide.org/basic-syntax/) and [extended syntax](https://www.markdownguide.org/extended-syntax/).

---

## Basic Syntax

These are the elements outlined in John Gruber’s original design document. All Markdown applications support these elements.

---

### Heading

Source: 

    # Heading1
    ## Heading2
    ### Heading3

Result:  

# H1
## H2
### H3

---

### Bold

Source: 

`**bold text**`

Result:  

**bold text**

---

### Italic

Source: 

`*italicized text*`

*italicized text*

---

### Blockquote

Source: 

`> blockquote`

Result:  

> blockquote

---

### Ordered List

Source: 

    1. First item
    2. Second item
    3. Third item

Result:  

1. First item
2. Second item
3. Third item

---

### Unordered List

Source: 

    - First item
    - Second item
    - Third item

Result:  

- First item
- Second item
- Third item

---

### Code

Source: 

    `code`

Result:  

`code`

---

### Horizontal Rule

Source: 

`---`

Result:  

---

(yes, again!)

---

### Link

Source: 

`[DocMD Website](https://docmd.us)`

Result:  

[DocMD Website](https://docmd.us)

---

### Image

Source: 

`![alt text](https://docmd.us/static/img/logo.png)`

Result:  

![alt text](https://docmd.us/static/img/logo.png)

---

## Extended Syntax

These elements extend the basic syntax by adding additional features. Not all Markdown applications support these elements.

---

### Table

Source: 

    | Syntax | Description |
    | ----------- | ----------- |
    | Header | Title |
    | Paragraph | Text |

Result:  

| Syntax | Description |
| ----------- | ----------- |
| Header | Title |
| Paragraph | Text |

---

### Fenced Code Block

Source: 

```
{
  "firstName": "John",
  "lastName": "Smith",
  "age": 25
}
```

Result:  

```
{
  "firstName": "John",
  "lastName": "Smith",
  "age": 25
}
```

---

### Footnote

Source: 

`Here's a sentence with a footnote. [^1]`

`[^1]: This is the footnote.`

Result:  

Here's a sentence with a footnote. [^1]

[^1]: This is the footnote.

---

### Heading ID

Source: 

`#### My Great Heading {#custom-id}`

Result:  

#### My Great Heading {#custom-id}

---

### Definition List

Source: 

    term
    : definition

Result:  

term
: definition

---

### Strikethrough

Source: 

`~~The world is flat.~~`

Result:  

~~The world is flat.~~

---

### Task List

Source: 

    - [x] Write the press release
    - [ ] Update the website
    - [ ] Contact the media

Result:  

- [x] Write the press release
- [ ] Update the website
- [ ] Contact the media

---

### Emoji

Source: 

`That is so funny! :joy:`

Result:  

That is so funny! :joy:

(See also [Copying and Pasting Emoji](https://www.markdownguide.org/extended-syntax/#copying-and-pasting-emoji))

---

### Highlight

Source: 

`I need to highlight these ==very important words==.`

Result:  

I need to highlight these ==very important words==.

---

### Subscript

Source: 

`H~2~O`

Result:  

H~2~O

---

### Superscript

Source: 

`X^2^`

Result:  

X^2^

---


## References

This page is strongly inspired by and based on [The Markdown Guide](https://www.markdownguide.org), who we thank warmly ;)

Here are more handy resources:  

- [CommonMark Reference](https://commonmark.org/help/) - A straightforward guide to the standard Markdown spec.  
- [GitHub Flavored Markdown (GFM)](https://github.github.com/gfm/) - Official spec for GitHub’s Markdown flavor.  
- [Daring Fireball: Markdown Syntax](https://daringfireball.net/projects/markdown/syntax) - John Gruber’s original Markdown documentation.  
- [Markdown Tutorial](https://www.markdowntutorial.com/) - Interactive lessons for hands-on learning.  
- [Basic Markdown Syntax by It’s FOSS](https://itsfoss.com/markdown-guide/) - Beginner-friendly guide with a free cheat sheet download.  
