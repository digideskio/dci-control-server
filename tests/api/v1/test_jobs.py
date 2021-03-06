# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2016 Red Hat, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import unicode_literals
import pytest


def test_create_jobs(admin, jobdefinition_id, team_id, remoteci_id,
                     components_ids):
    data = {'jobdefinition_id': jobdefinition_id, 'team_id': team_id,
            'remoteci_id': remoteci_id, 'comment': 'kikoolol',
            'components': components_ids}
    job = admin.post('/api/v1/jobs', data=data)
    job_id = job.data['job']['id']

    assert job.status_code == 201
    assert job.data['job']['comment'] == 'kikoolol'

    job = admin.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200
    assert job.data['job']['comment'] == 'kikoolol'


def test_create_jobs_empty_comment(admin, jobdefinition_id, team_id,
                                   remoteci_id, components_ids):
    data = {'jobdefinition_id': jobdefinition_id, 'team_id': team_id,
            'remoteci_id': remoteci_id, 'components': components_ids}
    job = admin.post('/api/v1/jobs', data=data).data
    assert job['job']['comment'] is None

    job = admin.get('/api/v1/jobs/%s' % job['job']['id']).data
    assert job['job']['comment'] is None


def test_schedule_jobs(admin, jobdefinition_id, team_id, remoteci_id,
                       topic_id):
    headers = {
        'User-Agent': 'thisismyuseragent',
        'Client-Version': 'python-dciclient_0.1.0'
    }
    job = admin.post('/api/v1/jobs/schedule', headers=headers,
                     data={'remoteci_id': remoteci_id,
                           'topic_id': topic_id})
    assert job.status_code == 201
    job = job.data['job']
    assert job['jobdefinition_id'] == jobdefinition_id
    assert job['team_id'] == team_id
    assert job['remoteci_id'] == remoteci_id
    assert job['user_agent'] == headers['User-Agent']
    assert job['client_version'] == headers['Client-Version']


def test_schedule_job_recheck(admin, job_id, remoteci_id, topic_id):
    job_rechecked = admin.post('/api/v1/jobs/%s/recheck' % job_id).data['job']
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': topic_id})
    assert job_scheduled.status_code == 201
    job_scheduled = job_scheduled.data['job']
    assert job_scheduled['id'] == job_rechecked['id']


def test_schedule_job_with_new_topic(admin, remoteci_id, team_admin_id):
    # create a new topic and schedule a new job
    data = {'name': 'new_topic'}
    pt = admin.post('/api/v1/topics', data=data).data
    new_topic_id = pt['topic']['id']

    # The team does not belongs to topic yet
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': new_topic_id})
    assert job_scheduled.status_code == 412

    # Add the team to the topic
    admin.post('/api/v1/topics/%s/teams' % new_topic_id,
               data={'team_id': team_admin_id})

    # There is no jobdefinition for this topic yet
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': new_topic_id})
    assert job_scheduled.status_code == 412

    # Create a jobdefinition for this topic
    data = {'topic_id': new_topic_id, 'name': 'name-ct', 'type': 'type_1'}
    cmpt = admin.post('/api/v1/components', data=data).data

    data = {'name': 'pname', 'topic_id': new_topic_id,
            'component_types': ['type_1']}
    jd = admin.post('/api/v1/jobdefinitions', data=data).data
    jd_id = jd['jobdefinition']['id']

    data = {'component_id': cmpt['component']['id']}
    admin.post('/api/v1/jobdefinitions/%s/components' % jd_id, data=data)

    # now schedule a job on that new topic
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': new_topic_id})
    assert job_scheduled.status_code == 201
    job = job_scheduled.data['job']
    assert job['jobdefinition_id'] == jd_id


def test_schedule_job_with_remoteci_deactivated(admin, remoteci_id, topic_id):
    admin.put('/api/v1/remotecis/%s' % remoteci_id, data={'active': False})
    job_scheduled = admin.post('/api/v1/jobs/schedule',
                               data={'remoteci_id': remoteci_id,
                                     'topic_id': topic_id})
    assert job_scheduled.status_code == 412


def test_schedule_jobs_not_active(admin, jobdefinition_id, team_id,
                                  remoteci_id, topic_id):
    """No active jobdefinition

    Only one inactive jobdefinition, scheduler should return::

        No jobs available for run (412).
    """
    jd = admin.get('/api/v1/jobdefinitions/%s' % jobdefinition_id).data
    ppt = admin.put('/api/v1/jobdefinitions/%s' % jobdefinition_id,
                    data={'active': False},
                    headers={'If-match': jd['jobdefinition']['etag']})
    assert ppt.status_code == 204
    job = admin.post('/api/v1/jobs/schedule',
                     data={'remoteci_id': remoteci_id,
                           'topic_id': topic_id})
    assert job.status_code == 412


def test_schedule_kill_old_jobs(admin, jobdefinition_factory, remoteci_id,
                                topic_id):
    """when a job is scheduled for a remoteci, the old ones must be killed."""
    jobdefinition_factory('1st')
    jobdefinition_factory('2nd')
    jobdefinition_factory('3rd')

    r = admin.post('/api/v1/jobs/schedule',
                   data={'remoteci_id': remoteci_id,
                         'topic_id': topic_id})
    r.status_code == 201
    r = admin.post('/api/v1/jobs/schedule',
                   data={'remoteci_id': remoteci_id,
                         'topic_id': topic_id})

    # Create a bunch of recheck jobs
    assert r.status_code == 201
    job_id = r.data['job']['id']
    assert admin.post('/api/v1/jobs/%s/recheck' % job_id).status_code == 201
    assert admin.post('/api/v1/jobs/%s/recheck' % job_id).status_code == 201

    # Finally call the scheduler
    assert admin.post('/api/v1/jobs/schedule',
                      data={'remoteci_id': remoteci_id,
                            'topic_id': topic_id}).status_code == 201

    # all the jobs but the last one should be killed
    jobs = admin.get('/api/v1/jobs?sort=created_at').data
    assert jobs['jobs'][0]['status'] == 'killed'
    assert jobs['jobs'][1]['status'] == 'killed'
    assert jobs['jobs'][2]['status'] == 'killed'
    assert jobs['jobs'][3]['status'] == 'new'


def test_schedule_give_latest_components(admin, jobdefinition_factory,
                                         remoteci_id, topic_id):
    """The scheduled job should come with the last components."""
    def components_from_job():
        jobdefinition_factory('1st')
        r = admin.post('/api/v1/jobs/schedule',
                       data={'remoteci_id': remoteci_id,
                             'topic_id': topic_id})
        job_id = r.data['job']['id']
        component_url = '/api/v1/jobs/{job_id}/components'
        r = admin.get(component_url.format(job_id=job_id))
        return r.data['components']

    c1 = components_from_job()
    c2 = components_from_job()
    assert c1[0]['type'] == c2[0]['type']
    assert c1[0]['id'] != c2[0]['id']


def test_get_all_jobs(admin, jobdefinition_id, team_id, remoteci_id,
                      components_ids):
    job_1 = admin.post('/api/v1/jobs',
                       data={'jobdefinition_id': jobdefinition_id,
                             'team_id': team_id,
                             'remoteci_id': remoteci_id,
                             'components': components_ids})
    job_1_id = job_1.data['job']['id']

    job_2 = admin.post('/api/v1/jobs',
                       data={'jobdefinition_id': jobdefinition_id,
                             'team_id': team_id,
                             'remoteci_id': remoteci_id,
                             'components': components_ids})
    job_2_id = job_2.data['job']['id']

    db_all_jobs = admin.get('/api/v1/jobs?sort=created_at').data
    db_all_jobs = db_all_jobs['jobs']
    db_all_jobs_ids = [db_job['id'] for db_job in db_all_jobs]

    assert 'configuration' not in db_all_jobs[0]
    assert db_all_jobs_ids == [job_1_id, job_2_id]


def test_get_all_jobs_with_pagination(admin, jobdefinition_id, team_id,
                                      remoteci_id, components_ids):
    # create 4 jobs and check meta count
    data = {'jobdefinition_id': jobdefinition_id,
            'team_id': team_id,
            'remoteci_id': remoteci_id,
            'components': components_ids}
    admin.post('/api/v1/jobs', data=data)
    admin.post('/api/v1/jobs', data=data)
    admin.post('/api/v1/jobs', data=data)
    admin.post('/api/v1/jobs', data=data)

    # check meta count
    jobs = admin.get('/api/v1/jobs').data
    assert jobs['_meta']['count'] == 4

    # verify limit and offset are working well
    jobs = admin.get('/api/v1/jobs?limit=2&offset=0').data
    assert len(jobs['jobs']) == 2

    jobs = admin.get('/api/v1/jobs?limit=2&offset=2').data
    assert len(jobs['jobs']) == 2

    # if offset is out of bound, the api returns an empty list
    jobs = admin.get('/api/v1/jobs?limit=5&offset=300')
    assert jobs.status_code == 200
    assert jobs.data['jobs'] == []


def test_get_all_jobs_with_embed(admin, jobdefinition_id, team_id,
                                 remoteci_id, components_ids):
    # create 2 jobs and check meta data count
    data = {'jobdefinition_id': jobdefinition_id,
            'team_id': team_id,
            'remoteci_id': remoteci_id,
            'components': components_ids}
    admin.post('/api/v1/jobs', data=data)
    admin.post('/api/v1/jobs', data=data)

    # verify embed with all embedded options
    query_embed = ('/api/v1/jobs?embed='
                   'team,remoteci,jobdefinition')
    jobs = admin.get(query_embed).data

    for job in jobs['jobs']:
        assert 'team_id' not in job
        assert 'team' in job
        assert job['team']['id'] == team_id
        assert 'jobdefinition_id' not in job
        assert 'jobdefinition' in job
        assert job['jobdefinition']['id'] == jobdefinition_id
        assert 'remoteci_id' not in job
        assert 'remoteci' in job
        assert job['remoteci']['id'] == remoteci_id

    # verify embed with jobdefinition.test nested
    query_embed = ('/api/v1/jobs?embed=jobdefinition')
    jobs = admin.get(query_embed).data

    for job in jobs['jobs']:
        assert 'jobdefinition_id' not in job
        assert 'jobdefinition' in job
        assert job['jobdefinition']['id'] == jobdefinition_id


def test_get_all_jobs_with_embed_not_valid(admin):
    jds = admin.get('/api/v1/jobs?embed=mdr')
    assert jds.status_code == 400


def test_update_job(admin, jobdefinition_id, team_id, remoteci_id,
                    components_ids):
    data = {
        'jobdefinition_id': jobdefinition_id,
        'team_id': team_id,
        'remoteci_id': remoteci_id,
        'comment': 'foo',
        'components': components_ids
    }
    job = admin.post('/api/v1/jobs', data=data)
    job = job.data['job']

    assert job['comment'] == 'foo'
    assert job['configuration'] == {}

    data_update = {'status': 'failure', 'comment': 'bar',
                   'configuration': {'ha': 'enabled'}}

    res = admin.put('/api/v1/jobs/%s' % job['id'], data=data_update,
                    headers={'If-match': job['etag']})

    assert res.status_code == 204

    res = admin.get('/api/v1/jobs/%s' % job['id'])
    job = res.data['job']

    assert res.status_code == 200
    assert job['status'] == 'failure'
    assert job['comment'] == 'bar'
    assert job['configuration'] == {'ha': 'enabled'}


def test_get_all_jobs_with_where(admin, jobdefinition_id, team_id,
                                 remoteci_id, components_ids):
    job = admin.post('/api/v1/jobs',
                     data={'jobdefinition_id': jobdefinition_id,
                           'team_id': team_id,
                           'remoteci_id': remoteci_id,
                           'components': components_ids})
    job_id = job.data['job']['id']

    db_job = admin.get('/api/v1/jobs?where=id:%s' % job_id).data
    db_job_id = db_job['jobs'][0]['id']
    assert db_job_id == job_id

    db_job = admin.get(
        '/api/v1/jobs?where=team_id:%s' % team_id).data
    db_job_id = db_job['jobs'][0]['id']
    assert db_job_id == job_id


def test_where_invalid(admin):
    err = admin.get('/api/v1/jobs?where=id')

    assert err.status_code == 400
    assert err.data == {
        'status_code': 400,
        'message': 'Invalid where key: "id"',
        'payload': {
            'error': 'where key must have the following form "key:value"'
        }
    }


def test_get_all_jobs_with_sort(admin, jobdefinition_id, team_id, remoteci_id,
                                components_ids):
    # create 3 jobs ordered by created time
    data = {'jobdefinition_id': jobdefinition_id,
            'team_id': team_id,
            'remoteci_id': remoteci_id,
            'components': components_ids}
    job_1 = admin.post('/api/v1/jobs', data=data).data['job']
    job_2 = admin.post('/api/v1/jobs', data=data).data['job']
    job_3 = admin.post('/api/v1/jobs', data=data).data['job']

    del job_1['configuration']
    del job_2['configuration']
    del job_3['configuration']

    jobs = admin.get('/api/v1/jobs?sort=created_at').data
    assert jobs['jobs'] == [job_1, job_2, job_3]

    # reverse order by created_at
    jobs = admin.get('/api/v1/jobs?sort=-created_at').data
    assert jobs['jobs'] == [job_3, job_2, job_1]


def test_get_job_by_id(admin, jobdefinition_id, team_id, remoteci_id,
                       components_ids):
    job = admin.post('/api/v1/jobs',
                     data={'jobdefinition_id': jobdefinition_id,
                           'team_id': team_id,
                           'remoteci_id': remoteci_id,
                           'components': components_ids})
    job_id = job.data['job']['id']

    job = admin.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200

    job = job.data
    assert job['job']['id'] == job_id


def test_get_jobstates_by_job_id(admin, job_id, team_id):
    data = {'status': 'new', 'job_id': job_id}
    jobstate_1 = admin.post('/api/v1/jobstates', data=data).data['jobstate']
    jobstate_2 = admin.post('/api/v1/jobstates', data=data).data['jobstate']

    jobstates = admin.get('/api/v1/jobs/%s/jobstates' % job_id)
    jobstates = jobstates.data['jobstates']

    assert jobstates[0]['id'] == jobstate_1['id']
    assert jobstates[1]['id'] == jobstate_2['id']


def test_get_job_not_found(admin):
    result = admin.get('/api/v1/jobs/ptdr')
    assert result.status_code == 404


def test_get_jobs_with_schedule(admin, topic_id, remoteci_id,
                                jobdefinition_id):
    # schedule a job
    data = {'remoteci_id': remoteci_id, 'topic_id': topic_id}
    job = admin.post('/api/v1/jobs/schedule', data=data)
    assert job.status_code == 201
    job_id = job.data['job']['id']

    # get the components of the scheduled jobs
    job_components = admin.get('/api/v1/jobs/%s/components' % job_id).data
    for c in job_components['components']:
        url = '/api/v1/topics/%s/components/%s/jobs' % (topic_id, c['id'])
        job = admin.get(url).data
        assert job['jobs'][0]['id'] == job_id


def test_job_recheck(admin, job_id):
    job_to_recheck = admin.get('/api/v1/jobs/%s' % job_id).data['job']
    job_rechecked = admin.post('/api/v1/jobs/%s/recheck' % job_id).data['job']
    assert job_rechecked['recheck'] is True
    assert (job_rechecked['jobdefinition_id'] ==
            job_to_recheck['jobdefinition_id'])
    assert job_rechecked['remoteci_id'] == job_to_recheck['remoteci_id']
    assert job_rechecked['team_id'] == job_rechecked['team_id']


def test_job_with_conf(admin, job_id):
    data = {'configuration': {'foo': 'bar'}}
    job = admin.get('/api/v1/jobs/%s' % job_id).data['job']
    admin.put('/api/v1/jobs/%s' % job['id'], data=data,
              headers={'If-match': job['etag']})
    job_to_recheck = admin.get('/api/v1/jobs/%s' % job_id).data['job']
    assert job_to_recheck['configuration']
    job_rechecked = admin.post('/api/v1/jobs/%s/recheck' % job_id).data['job']
    assert not job_rechecked['configuration']


def test_delete_job_by_id(admin, jobdefinition_id, team_id, remoteci_id,
                          components_ids):

    job = admin.post('/api/v1/jobs',
                     data={'jobdefinition_id': jobdefinition_id,
                           'team_id': team_id,
                           'remoteci_id': remoteci_id,
                           'components': components_ids})
    job_id = job.data['job']['id']
    job_etag = job.headers.get("ETag")
    assert job.status_code == 201

    job = admin.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200

    deleted_job = admin.delete('/api/v1/jobs/%s' % job_id,
                               headers={'If-match': job_etag})
    assert deleted_job.status_code == 204

    job = admin.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 404

# Tests for the isolation


def test_create_job_as_user(user, team_user_id, team_id, jobdefinition_id,
                            remoteci_user_id, components_ids):
    job = user.post('/api/v1/jobs',
                    data={'team_id': team_id,
                          'jobdefinition_id': jobdefinition_id,
                          'remoteci_id': remoteci_user_id,
                          'components': components_ids})
    assert job.status_code == 401

    job = user.post('/api/v1/jobs',
                    data={'team_id': team_user_id,
                          'jobdefinition_id': jobdefinition_id,
                          'remoteci_id': remoteci_user_id,
                          'components': components_ids})
    assert job.status_code == 201


@pytest.mark.usefixtures('job_id', 'job_user_id')
def test_get_all_jobs_as_user(user, team_user_id):
    jobs = user.get('/api/v1/jobs')
    assert jobs.status_code == 200
    assert jobs.data['_meta']['count'] == 1
    for job in jobs.data['jobs']:
        assert job['team_id'] == team_user_id


def test_get_job_as_user(user, team_user_id, job_id, jobdefinition_id,
                         remoteci_user_id, components_ids):
    job = user.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 404

    job = user.post('/api/v1/jobs',
                    data={'team_id': team_user_id,
                          'jobdefinition_id': jobdefinition_id,
                          'remoteci_id': remoteci_user_id,
                          'components': components_ids}).data
    job_id = job['job']['id']
    job = user.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 200


def test_job_recheck_as_user(user, job_id, remoteci_user_id, topic_user_id,
                             jobdefinition_factory):
    job = user.get('/api/v1/jobs/%s' % job_id)
    assert job.status_code == 404

    jobdefinition_factory(topic_id=topic_user_id)

    data = {'remoteci_id': remoteci_user_id,
            'topic_id': topic_user_id}
    job = user.post('/api/v1/jobs/schedule', data=data).data
    job_id = job['job']['id']
    job = user.post('/api/v1/jobs/%s/recheck' % job_id)

    assert job.status_code == 201


def test_delete_job_as_user(user, team_user_id, admin, job_id,
                            jobdefinition_id, remoteci_user_id,
                            components_ids):
    job = user.post('/api/v1/jobs',
                    data={'team_id': team_user_id,
                          'jobdefinition_id': jobdefinition_id,
                          'remoteci_id': remoteci_user_id,
                          'components': components_ids}).data
    job_user_id = job['job']['id']
    job = user.get('/api/v1/jobs/%s' % job_user_id)
    job_etag = job.headers.get("ETag")

    job_delete = user.delete('/api/v1/jobs/%s' % job_user_id,
                             headers={'If-match': job_etag})
    assert job_delete.status_code == 204

    job = admin.get('/api/v1/jobs/%s' % job_id)
    job_etag = job.headers.get("ETag")
    job_delete = user.delete('/api/v1/jobs/%s' % job_id,
                             headers={'If-match': job_etag})
    assert job_delete.status_code == 401


def test_create_file_for_job_id(user, jobdefinition_id, team_user_id,
                                remoteci_id, components_ids):
    # create a job
    job = user.post('/api/v1/jobs',
                    data={'jobdefinition_id': jobdefinition_id,
                          'team_id': team_user_id,
                          'remoteci_id': remoteci_id,
                          'components': components_ids})
    job_id = job.data['job']['id']
    assert job.status_code == 201

    # create a file
    headers = {'DCI-JOB-ID': job_id,
               'DCI-NAME': 'foobar'}
    file = user.post('/api/v1/files', headers=headers)
    file_id = file.data['file']['id']
    file = user.get('/api/v1/files/%s' % file_id).data
    assert file['file']['name'] == 'foobar'


@pytest.mark.usefixtures('file_job_user_id')
def test_get_file_by_job_id(user, job_id):
    url = '/api/v1/jobs/%s/files' % job_id

    # get file from job
    file_from_job = user.get(url)
    assert file_from_job.status_code == 200
    assert file_from_job.data['_meta']['count'] == 1


@pytest.mark.usefixtures('file_job_junit_user_id')
def test_get_results_by_job_id(user, job_id):
    url = '/api/v1/jobs/%s/results' % job_id

    # get file from job
    file_from_job = user.get(url)
    assert file_from_job.status_code == 200
    assert file_from_job.data['_meta']['count'] == 1
    assert file_from_job.data['results'][0]['total'] == '3'


@pytest.mark.usefixtures('file_job_junit_empty_user_id')
def test_get_empty_results_by_job_id(user, job_id):
    url = '/api/v1/jobs/%s/results' % job_id

    # get file from job
    file_from_job = user.get(url)
    assert file_from_job.status_code == 200
    assert file_from_job.data['_meta']['count'] == 1
    assert file_from_job.data['results'][0]['total'] == '0'


def test_job_search(user, jobdefinition_id, team_user_id, remoteci_id,
                    components_ids):

    # create a job
    job = user.post('/api/v1/jobs',
                    data={'jobdefinition_id': jobdefinition_id,
                          'team_id': team_user_id,
                          'remoteci_id': remoteci_id,
                          'components': components_ids})
    job_id = job.data['job']['id']
    job_etag = job.data['job']['etag']

    # update the configuration of a job
    data = {'configuration': {'ha': 'enabled', 'type': {'hw': 'baremetal'}}}
    user.put('/api/v1/jobs/%s' % job_id,
             data=data,
             headers={'If-match': job_etag})
    job_search_url = '/api/v1/jobs/search'

    # search with two values matching
    jobs_filtered = user.post(job_search_url,
                              data={'jobdefinition_id': jobdefinition_id,
                                    'configuration': {
                                        'ha': 'enabled',
                                        'type.hw': 'baremetal'}})
    assert jobs_filtered.data['_meta']['count'] == 1

    # search with two values not matched
    jobs_filtered = user.post(job_search_url,
                              data={'jobdefinition_id': jobdefinition_id,
                                    'configuration': {
                                        '_op': 'and',
                                        'ha': 'enabledd',
                                        'type.hw': 'baremetal'}})
    assert jobs_filtered.data['_meta']['count'] == 0

    # search with at least one value matching
    jobs_filtered = user.post(job_search_url,
                              data={'jobdefinition_id': jobdefinition_id,
                                    'configuration': {
                                        '_op': 'or',
                                        'ha': 'enabledd',
                                        'type.hw': 'baremetal'}})
    assert jobs_filtered.data['_meta']['count'] == 1
