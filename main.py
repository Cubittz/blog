import os
import re
import hashlib
import hmac
from string import letters
import random
import time
from urlparse import urlparse

import jinja2
import webapp2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                autoescape = True)

secret = 'd3re2bfrg4hrbbt'

##### helper functions

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        if self.user:
            params['welcome_message'] = 'Welcome ' + self.user.name
            params['welcome'] = '/'
            params['loginout_message'] = 'Logout'
            params['loginout'] = '/logout'
        else:
            params['welcome_message'] = 'Signup'
            params['welcome'] = '/signup'
            params['loginout_message'] = 'Login'
            params['loginout'] = '/login'
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

###### user
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE = re.compile(r"^[/S]+@[/S]+\.[\S]+$")
def valid_email(email):
    return not email or EMAIL_RE.match(email)

###### blog

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    author = db.StringProperty(required = False)

    def render(self, user):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self, user = user)

    def countLikes(self):
        p = self
        l = db.GqlQuery("SELECT * FROM Likes WHERE post = :1", p)
        return l.count()

    def userLikes(self, user):
        p = self
        u = user
        l = db.GqlQuery("SELECT * FROM Likes WHERE post = :1 AND user = :2", p, u)

        if l.count() > 0:
            return True

    def countComments(self):
        p = self
        c = db.GqlQuery("SELECT * FROM Comment WHERE post = :1", p)
        return c.count()

class Comment(db.Model):
    author = db.ReferenceProperty(User)
    post = db.ReferenceProperty(Post)
    comment = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class Likes(db.Model):
    user = db.ReferenceProperty(User)
    post = db.ReferenceProperty(Post)

class MainPage(Handler):
    def get(self):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC limit 10")
        self.render("index.html", posts = posts)

class Signup(Handler):
    def get(self):
        self.render("signup.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username, email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords don't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render("signup.html", **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError

class Register(Signup):
    def done(self):
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render("signup.html", error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/welcome')

class PostPage(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        comments = db.GqlQuery("SELECT * FROM Comment WHERE post = :1 ORDER BY created DESC", key)
        post.comments = comments.count()

        user = self.user
        self.render("blogentry.html", p = post, comments = comments, user = user)

class NewPage(Handler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect('/signup')

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject=subject, content = content, author = self.user.name)
            p.put()
            self.redirect('/%s' % str(p.key().id()))
        else:
            error = "subject and content, pelase!"
            self.render("newpost.html", subject = subject, content = content, error = error)

class EditPage(Handler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        self.render('editpost.html', post = post)

    def post(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/%s' % post_id)
        else:
            error = "subject and content, pelase!"
            self.render("editpost.html", subject = subject, content = content, error = error)

class DeletePage(Handler):
    def post(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        post = db.get(key)

        likes = db.GqlQuery("SELECT * FROM Likes WHERE post = :1", post)
        if likes.count() > 0:
            db.delete(likes)

        comments = db.GqlQuery("SELECT * FROM Comment WHERE post = :1", post)
        if comments.count() > 0:
            db.delete(comments)

        db.delete(post)
        time.sleep(0.2)

        self.redirect('/')

class CommentHandler(Handler):
    def post(self, post_id):
        comment = self.request.get('comment')
        if comment:
            if self.user:
                key = db.Key.from_path('Post', int(post_id), parent=blog_key())
                post = db.get(key)
                user = self.user

                c = Comment(parent = blog_key(), author = user, post = post, comment = comment)
                c.put()

                self.redirect('/%s' % post_id)
            else:
                msg = "You must log on before you can leave a comment"
                self.render('login.html', error = msg, url = post_id)
        else:
            msg = "Please enter a meaningful comment!"
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)

            comments = db.GqlQuery("SELECT * FROM Comment WHERE post = :1 ORDER BY created DESC", key)
            post.comments = comments.count()

            user = self.user
            self.render("blogentry.html", p = post, comments = comments, user = user, error = msg)

class DeleteComment(Handler):
    def post(self, comment_id):
        key = db.Key.from_path('Comment', int(comment_id), parent=blog_key())
        comment = db.get(key)
        post = comment.post.key().id()

        db.delete(comment)
        time.sleep(0.2)

        self.redirect('/%s' % post)

class EditComment(Handler):
    def post(self, comment_id):
        key = db.Key.from_path('Comment', int(comment_id), parent=blog_key())
        c = db.get(key)
        post = c.post.key().id()
        comment = self.request.get('editComment%s' % comment_id)
        if comment:
            c.comment = comment
            c.put()

        self.redirect('/%s' % post)

class LikeHandler(Handler):
    def post(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id), parent=blog_key())
            post = db.get(key)
            user = self.user

            likes = db.GqlQuery("SELECT * FROM Likes WHERE post = :1 AND user = :2", post, user)
            if likes.count() > 0:
                db.delete(likes)
            else:
                l = Likes(parent = blog_key(), user = user, post = post)
                l.put()

            self.redirect('/%s' % post_id)
        else:
            msg = 'You must log in before you can like a post'
            self.render('login.html', error = msg, url = post_id)

class Login(Handler):
    def get(self):
        self.render('login.html')

    def post(self):
        url = '/'
        url += self.request.get('url')
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            time.sleep(0.2)
            self.redirect(url)
        else:
            msg = 'Invalid Login'
            self.render('login.html', error = msg)

class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect('/login')

class Welcome(Handler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/signup')

app = webapp2.WSGIApplication([('/', MainPage),
                                ('/signup', Register),
                                ('/login', Login),
                                ('/logout', Logout),
                                ('/welcome', Welcome),
                                ('/newpost', NewPage),
                                ('/edit/([0-9]+)', EditPage),
                                ('/delete/([0-9]+)', DeletePage),
                                ('/comment/([0-9]+)', CommentHandler),
                                ('/comment/delete/([0-9]+)', DeleteComment),
                                ('/comment/edit/([0-9]+)', EditComment),
                                ('/like/([0-9]+)', LikeHandler),
                                ('/([0-9]+)', PostPage)]
                                , debug = True)