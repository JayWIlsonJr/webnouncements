import datetime

import webapp2

from ..supports.main import Handler
from ..supports.tables import Post

static_location = '/display'
'''
class Display(Handler):
    def get(self):
        school = self.request.get('school')
        template = self.request.get('template')
        date = self.request.get('date')
        Post.query(
            Post.schoolUUID == school,
            Post.startDate <= date if date else
        ).order(-Post.)
'''
class Today(Handler):
    def get(self):
        today = datetime.datetime.now().date()
        school = self.request.get('s')
        posts = Post.query(Post.school_uuid == school).filter(Post.startDate <= today).fetch()
        for post in list(posts):
            if not post.endDate >= today:
                posts.remove(post)

        self.renderBlank('display.html', posts = posts)

app = webapp2.WSGIApplication([
    (static_location + '/today', Today)
], debug=True)
