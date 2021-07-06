import os
import json

from flask import (
    Flask,
    jsonify,
    send_from_directory,
    request,
    redirect,
    url_for
)
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

#import flask.scaffold
#flask.helpers._endpoint_from_view_func = flask.scaffold._endpoint_from_view_func # fix
from flask_restx import Api, Resource, fields, abort, reqparse

from flask_socketio import SocketIO

import canonizer


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0',
          title='API services',
          description='REST API for canonizer')
ns = api.namespace('rest_api', description='REST services API')
socketio = SocketIO(app)


canonizer_input = api.model('CanonizerInput', {
    'forms': fields.List(fields.String, required=True, description='list of input forms')
})
canonizer_output = api.model('CanonizerOutput', {
    'canonical_forms': fields.List(fields.String, description='list of canonical forms')
})


@ns.route('/canonize')
class Canonizer(Resource):
    @ns.doc('compute canonical forms')
    @ns.expect(canonizer_input, validate=True)
    @ns.marshal_with(canonizer_output)
    def post(self):
        return {'canonical_forms': canonizer.process(api.payload['forms'])}


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=True)
