import os

import jinja2
import webapp2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                autoescape = True) 

class Blog(db.Model):
    title = db.StringProperty(required = True)
    blogContent = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(Handler):
    def get(self):
        self.render("index.html")

class NewPage(Handler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        title = self.request("title")
        blogContent = self.request("blogContent")

        b = Blog(title = title, blogContent = blogContent)
        b.put()
        self.redirect('/')

app = webapp2.WSGIApplication([('/', MainPage),
                                ('/New', NewPage)]
                                , debug = True)