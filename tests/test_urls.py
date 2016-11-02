from nose.tools import assert_equal, assert_is_instance, assert_in
from mock import MagicMock

import gluuwebui
import requests
import json

gluuwebui.app.config['TESTING'] = True
app = gluuwebui.app.test_client()

resources = ['/providers', '/clusters', '/nodes', '/license_keys',
             '/containers', '/container_logs']

##############################################################################
#   Handling GET requests and ensuring all /resource /resource/id are answered


def mock_get(code):
    """Mocks the API server by patching all GET requests with
     status_code=200, json() = {} response"""
    requests.get = MagicMock()
    requests.get.return_value.status_code = code
    if code == 200:
        requests.get.return_value.json.return_value = {}
    else:
        requests.get.return_value.json.return_value = {'message': 'MockError'}
    requests.get.return_value.reason = "Mock Reason"


def check_get_ok(item):
    res = app.get(item)
    assert_equal(200, res.status_code)


def check_get_error(item):
    res = app.get(item)
    assert_equal(res.status_code, 400)
    assert_is_instance(json.loads(res.data)['message'], unicode)


def test_resources_get():
    """Tests gluuwebui responses for GET /resource and /resource/id"""
    mock_get(200)
    check_get_ok('/')
    for item in resources:
        yield check_get_ok, item
        yield check_get_ok, item+"/some_id"

    mock_get(400)
    for item in resources:
        yield check_get_error, item
        yield check_get_error, item+"/dummy_id"


##############################################################################
#   Test POST requests to resource points return a json
#   Success: resource_id or logfile, code 200
#   Failure: message, code 400

post_calls = ['/clusters', '/containers/type', '/license_keys', '/nodes/type',
              '/providers/driver']


def mock_post(code):
    """Mocks API server POST response"""
    requests.post = MagicMock(name='post')
    requests.post.return_value.status_code = code

    # also mock the save node log funtion to avoid unnecessary writes
    gluuwebui.views.append_history = MagicMock(name='save_node_log')
    if code == 204:
        requests.post.return_value.json.return_value = {'id': 'mock_id',
                                                        'name': 'mock_name',
                                                        }
    else:
        requests.post.return_value.json.return_value = {'message': 'MockError'}
    requests.post.return_value.reason = "Mock Reason"


def check_post_success(item):
    p = app.post(item, data='{"public_key": "key"}')  # pub_key for lic post
    assert_equal(p.status_code, 200)
    if item == '/node':
        assert_is_instance(json.loads(p.data)['log'], unicode)
    else:
        assert_is_instance(json.loads(p.data)['id'], unicode)


def check_post_error(item):
    p = app.post(item, data='{"public_key": "key"}')
    assert_equal(p.status_code, 400)
    assert_is_instance(json.loads(p.data)['message'], unicode)


def test_resources_post():
    mock_post(204)
    for item in post_calls:
        yield check_post_success, item

    mock_post(400)
    for item in post_calls:
        yield check_post_error, item

#############################################################################
# Test for the update requests POST /resource/id from browser and PUT /r/id
# from the gluu webui to the API server


def mock_put(code):
    requests.put = MagicMock('put')
    requests.put.return_value.status_code = code
    if code == 200:
        requests.put.return_value.json.return_value = {'code': 'your-code'}
    else:
        requests.put.return_value.json.return_value = {'message': 'MockError'}
        requests.put.return_value.reason = "Mock Reason"


def check_put_success(item):
    res = app.put(item + '/some_id', data='{"id":"some_id"}')
    assert_equal(res.status_code, 200)


def check_put_error(item):
    res = app.put(item + '/some_id', data='{}')
    assert_equal(res.status_code, 405)


def test_resource_update():
    mock_put(200)
    for item in resources:
        if item == '/license_keys':
            yield check_put_success, item
        elif not item == '/nodes':
            yield check_put_error, item

    mock_put(202)
    check_put_success('/nodes')


#############################################################################
#  Tests for DELETE requests to /resource/id


def mock_delete(code):
    requests.delete = MagicMock('delete')
    requests.delete.return_value.status_code = code
    if code > 210:
        requests.delete.return_value.json.return_value = {'message': 'MockMsg'}
    requests.delete.return_value.reason = 'Mock Reason'


def check_delete(item, code):
    r = app.delete("{0}/some_id".format(item))
    assert_equal(r.status_code, code)


def test_resource_delete():
    mock_delete(204)
    for item in resources:
        yield check_delete, item, 200

    mock_delete(400)
    for item in resources:
        yield check_delete, item, 400


def test_delete_parses_forcerm_querystring():
    requests.delete = MagicMock('delete')
    requests.delete.return_value.status_code = 204
    requests.delete.return_value.reason = 'Mock Reason'
    r = app.delete("/containers/some-id?force_rm=1")
    assert_equal(r.status_code, 200)
    requests.delete.assert_called_once_with(
        gluuwebui.app.config["API_SERVER_URL"]+"containers/some-id?force_rm=1")

    r = app.delete("/containers/some-id?force_rm=0")
    assert_equal(r.status_code, 200)
    requests.delete.assert_called_with(
        gluuwebui.app.config["API_SERVER_URL"]+"containers/some-id?force_rm=0")


##############################################################################
#   Check for static file redirects


def test_static_redirects():
    statics = ['js', 'css', 'img']
    for folder in statics:
        ro = app.get("/{0}/{1}".format(folder, 'testfile.txt'))  # existing file
        assert_equal(ro.status_code, 200)
        assert_equal('Test Assets', ro.data)

        ro = app.get("/{0}/{1}".format(folder, 'non_existant_file.txt'))
        assert_equal(ro.status_code, 200)
        assert_in('No such file or directory', ro.data)


def test_templates():
    ro = app.get("templates/new_provider.html")  # existing file
    assert_equal(ro.status_code, 200)
    assert_in('form', ro.data)

    ro = app.get("templates/non_existant_file.html")
    assert_equal(ro.status_code, 200)
    assert_in('No such file or directory', ro.data)
