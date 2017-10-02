import os
import boto3
import tornado.ioloop
import tornado.web
import tornado.log

from dotenv import load_dotenv
from jinja2 import \
  Environment, PackageLoader, select_autoescape

load_dotenv(".env")

PORT = int(os.environ.get('PORT', '8888'))

GIT_REV = os.environ.get('GIT_REV', 'NONE')
print(GIT_REV)
ENV = Environment(
  loader=PackageLoader('app', 'templates'),
  autoescape=select_autoescape(['html', 'xml'])
)

SES_CLIENT = boto3.client(
    'ses',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'),
    region_name="us-east-1"
)

class TemplateHandler(tornado.web.RequestHandler):
  def render_template (self, tpl, context):
    template = ENV.get_template(tpl)
    context['GIT_REV'] = GIT_REV
    self.write(template.render(**context))

class MainHandler(TemplateHandler):
  def get(self):
    self.set_header(
      'Cache-Control',
      'no-store, no-cache, must-revalidate, max-age=0')
    self.render_template("index.html", {'name': 'World'})

class CityHandler(TemplateHandler):
    def get (self, city):
        self.set_header(
          'Cache-Control',
          'no-store, no-cache, must-revalidate, max-age=0')
        self.render_template(city + ".html", {'city': city})

class FormHandler(TemplateHandler):
  def post (self):
    firstname = self.get_body_argument('firstname')
    lastname = self.get_body_argument('lastname')
    email = self.get_body_argument('email')
    message = self.get_body_argument('message')

    response = SES_CLIENT.send_email(
      Destination={
        'ToAddresses': ['monisriz@gmail.com'],
      },
      Message={
        'Body': {
          'Text': {
            'Charset': 'UTF-8',
            'Data': 'First Name: {}\nLast Name: {}\nEmail: {}\nMessage: {}\n'.format(firstname, lastname, email, message),
          },
        },
        'Subject': {'Charset': 'UTF-8', 'Data': 'Travel Page Section'},
      },
      Source='contact@monisrizvi.com',
    )

    self.redirect('submit.html?firstname=' + firstname)

  def get(self):
    self.set_header(
      'Cache-Control',
      'no-store, no-cache, must-revalidate, max-age=0')
    self.render_template("form.html", {"firstname":{}})


class SubmitHandler(TemplateHandler):
  def get(self):
    name = self.get_query_argument('firstname')
    self.set_header(
      'Cache-Control',
      'no-store, no-cache, must-revalidate, max-age=0')
    self.render_template("submit.html", {'firstname': name})

  def post (self):
      name = self.get_body_argument('firstname')


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/form.html", FormHandler),
        (r"/submit.html",SubmitHandler),
        (r"/(.*).html", CityHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {'path': 'static'})
    ], autoreload=True)


if __name__ == "__main__":
    tornado.log.enable_pretty_logging()
    app = make_app()
    app.listen(PORT, print('Server started on localhost:' + str(PORT)))
    tornado.ioloop.IOLoop.current().start()
