import sh
import os
import json
import dateutil.parser as parser

import xml.dom.minidom

def get_ancestry(ancestors, k):
  a = child_ancestry[k]
  if a != "":
    ancestors.insert(0, a.zfill(12))
    get_ancestry(ancestors, a)

doc = xml.dom.minidom.parse("comments.xml")

articles = {}

# Collect articles
for article in doc.getElementsByTagName("thread"):
  id = article.getAttribute("dsq:id").strip()

  try:
    link = article.getElementsByTagName("link")[0].firstChild.nodeValue.strip()
  except IndexError:
    continue

  # don't know why some articles have a query string.
  if "?" in link:
    link = link.split("?")[0]

  # 1970/ is my drafts folder
  if "/1970/" in link or "web.archive.org/" in link:
    continue

  # Normalize the http and https prefixed IDs
  if "https://matienzo.org" in link or "http://matienzo.org" in link:
    link = link.replace("http://matienzo.org","").replace("https://matienzo.org", "")
    if id not in articles:
        articles[id] = { "link": link}

child_ancestry = {}

# Collect Comments
for post in doc.getElementsByTagName("post"):

  article = post.getElementsByTagName("thread")[0].getAttribute("dsq:id").strip()

  if article in articles:

    if "true" in "" + post.getElementsByTagName("isSpam")[0].firstChild.nodeValue:
        continue
    if "true" in "" + post.getElementsByTagName("isDeleted")[0].firstChild.nodeValue:
        continue

    parent = post.getElementsByTagName("parent")
    if len(parent) > 0:
        parent = parent[0].getAttribute("dsq:id")
    else:
        parent = ""

    postId = post.getAttribute("dsq:id")

    child_ancestry[postId] = parent

    if "posts" not in articles[article]:
      articles[article]["posts"] = {}

    articles[article]["posts"][postId] = {
          "date": post.getElementsByTagName("createdAt")[0].firstChild.nodeValue,
      "name": post.getElementsByTagName("name")[0].firstChild.nodeValue,
      "comment": post.getElementsByTagName("message")[0].firstChild.nodeValue,
      "path": articles[article]["link"]
    }

articles_with_comments = {}

# Only articles with comments
for article_key, article in articles.items():
  if "posts" in article:
    articles_with_comments[article_key] = article

for article_key, article in articles_with_comments.items():
  for post_article_key, post in articles_with_comments[article_key]["posts"].items():
    if "posts" not in articles_with_comments[article_key]:
      articles_with_comments[article_key]["posts"] = {}
    articles_with_comments[article_key]["posts"][post_article_key] = post
    ancestors = []
    ancestors.insert(0, post_article_key.zfill(12))
    get_ancestry(ancestors, post_article_key)

    articles_with_comments[article_key]["posts"][post_article_key]["order"] = ",".join(ancestors)
    articles_with_comments[article_key]["posts"][post_article_key]["indent"] = len(ancestors) -1


# Change posts from a dict to a list
dump = {}
for article_key, article in articles_with_comments.items():
  article["posts"] = article["posts"].values()
  dump[article["link"]] = article["posts"]

print json.dumps(dump)

for article_key, article in articles_with_comments.items():
  file = open("disqusoutput/" + article["link"].replace("/","-").replace(".","-") + ".json", "w")
  file.write(json.dumps(list(article["posts"]), indent=4, sort_keys=True))
  file.close()


# Actual HTML output.
for article_key, article in articles_with_comments.items():
  file = open("disqusoutput/" + article["link"].replace("/", "-").replace(".","-") + ".html", "w")
  file.writelines("<h2>Comments formerly in Disqus, but exported and mounted statically ...</h2><br/>")
  file.writelines("<table class='table table-striped'>\n")
  for post in sorted(article["posts"], key=lambda x: x['order']):
    w = str(50 * post["indent"])
    file.writelines("<tr><td style='padding-left: " + w + "px' class='dTS'>" + post["date"] + "</td><td class='dU'>" + post["name"] + "</td></tr>\n")
    file.writelines("<tr><td style='padding-left: " + w + "px' colspan='2' class='dMessage'>" + post["comment"].encode('utf-8') + "</td></tr>\n")
  file.writelines("</table>\n")
  file.close()
