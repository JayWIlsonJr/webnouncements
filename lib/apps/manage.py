import json
import logging
from datetime import datetime
from uuid import uuid4

import webapp2

from google.appengine.ext import ndb
from google.appengine.api import users

from ..supports.dater import poster
from ..supports.main import Handler
from ..supports.tables import Post, SchoolAccount, Invite, School, Account
from ..supports.constants import time_delta, dateTimePattern, dateConvertPattern

static_location = '/manage'

class Manage(Handler):
    def get(self):
        user = users.get_current_user()
        school = self.request.get("sc")
        schoolInfo, linkInfo = SchoolAccount.getLinkSC(user.user_id(), school)
        people = SchoolAccount.query(SchoolAccount.school_uuid == schoolInfo.uuid).fetch()
        usersInfo = []
        for account in people:
            usersInfo.append(Account.query(Account.user_id == account.user_id).fetch(1)[0])
            usersInfo[-1].role = account.role
        self.render('manage/manage.html', users=usersInfo, school_uuid=schoolInfo.uuid)

class DeleteUser(Handler):
    def post(self):
        user = users.get_current_user()

        data = json.loads(self.request.body)

        if data['uuid'] and data['school_uuid']:
            schoolAccountQuery = SchoolAccount.query(SchoolAccount.school_uuid == data['school_uuid'], SchoolAccount.user_id == user.user_id()).fetch()
            if len(schoolAccountQuery) > 0:
                role = schoolAccountQuery[0].role
                if role == "admin":
                    deleteAccountQuery = SchoolAccount.query(SchoolAccount.school_uuid == data['school_uuid'], SchoolAccount.user_id == data['uuid']).fetch(1)
                    if len(deleteAccountQuery) == 1:
                        deleteAccount = deleteAccountQuery[0]
                        deleteAccount.key.delete()
                        logging.info("The user '%s' that belonged to '%s' was deleted by '%s'" % (deleteAccount.user_id, schoolAccountQuery[0].school_uuid, user.user_id()))
                        self.respondToJson({'success': 'true',
                                            'message': 'The user %s was deleted.' % data['uuid']})
                    else:
                        logging.error("The user '%s' could not be delete because it did not exist in school '%s'" % (data['uuid'], data['school_uuid']))
                        self.respondToJson({'success': 'false', 'message': 'Account not found!'})
                else:
                    logging.warning("The user '%s' has tried to acess management screen for school '%s', howerver they are not admin of school." % (user.user_id(), schoolAccountQuery[0].school_uuid))
                    self.respondToJson({'success': 'false', 'message': 'Your not an admin for this school!'})
            else:
                logging.warning("The user did not send all data.")
                self.respondToJson({'success': 'false', 'message': "You shouldn't be here."})

class MngPost(Handler):
    def get(self):
        user = users.get_current_user()

        schoolUuid = self.request.get("sid")

        schoolAccountQuery = SchoolAccount.query(SchoolAccount.school_uuid == schoolUuid, SchoolAccount.user_id == user.user_id()).fetch()
        schoolAccount = schoolAccountQuery[0] if len(schoolAccountQuery) > 0 else None
        if schoolAccount:
            today = datetime.now()
            #today += datetime.timedelta(hours=time_delta)
            requests = Post.query(Post.school_uuid == schoolUuid, Post.approved == False, Post.denied == False, Post.endDate >= today).fetch(50)
            posts = Post.query(Post.school_uuid == schoolUuid, Post.approved == True, Post.endDate >= today).fetch(50)

            self.render("manage/post.html", posts=posts, requests=requests, school_uuid = schoolAccount.school_uuid)
        else:
            self.render('cloud.html', error="You do not belong to this school.")

class EditPost(Handler):
    def get(self):
        user = users.get_current_user()
        postID = self.request.get("pid")
        schoolID = self.request.get("sid")

        postQueryInfo = Post.query(Post.uuid == postID, Post.school_uuid == schoolID).fetch()
        post = postQueryInfo[0] if len(postQueryInfo) > 0 else None

        if post and SchoolAccount.verifyLink(user.user_id(), schoolID):
            schoolQueryInfo = School.query(School.uuid == post.school_uuid).fetch()
            schoolInfo = schoolQueryInfo[0] if len(schoolQueryInfo) > 0 else None
            if schoolInfo:
                self.render("submit/submit.html",
                                school_code = schoolInfo.school_code,
                                title=post.title,
                                text=post.text,
                                startDate = post.startDate.strftime(dateTimePattern),
                                endDate = datetime.strftime(post.endDate, dateTimePattern),
                                readStartDate = datetime.strftime(post.readStartDate, dateTimePattern) if post.readStartDate else None,
                                readEndDate = datetime.strftime(post.readEndDate, dateTimePattern) if post.readEndDate else None,
                                link=static_location + '/edit',
                                postID = post.uuid,
                            )

    def post(self):
        poster(self, new = False)

app = webapp2.WSGIApplication([
    (static_location + '/main', Manage),
    (static_location + '/delete', DeleteUser),
    (static_location + '/post', MngPost),
    (static_location + '/edit', EditPost),
], debug=True)
