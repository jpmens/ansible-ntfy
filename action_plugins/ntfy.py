#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, by Jan-Piet Mens

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: ntfy
short_description: Send push notifications to ntfy
description:
  - Sends push notifications to your phone or desktop via C(POST) requests and the C(ntfy.sh) open source program.
options:
  msg:
    description:
      - The body of the message to be sent
    required: yes
    type: str
  topic:
    description:
      - I(Topic) (in ntfy parlance) to send messages to. If C(topic) is not specified as a parameter its value will be taken from play vars or finally from the default value. Note that I(ntfy) has no authentication so technically anybody can see what you post.
    default: "test-topic"
    type: str
  url:
    description:
      - URL to C(POST) messages to, if you host your own I(ntfy) or HTTP endpoint.
    type: str
    default: "https://ntfy.sh"
  attrs:
    description:
      - A optional dict of additional attributes to associate with C(msg). See EXAMPLES and https://ntfy.sh/docs/publish/ for details.
    type: str
    default: "none"
    required: no
author:
- Jan-Piet Mens (@jpmens)
'''

EXAMPLES = '''
- name: Report completion via ntfy
  ntfy:
    topic: "admin-alerts"
    msg: "Deployment on {{ inventory_hostname }} complete"

- name: Use our own endpoint
  ntfy:
    url: "http://localhost:8864/"
    msg: "thanks for all the fish"

- name: Add some bells and whistles
  ntfy:
    topic: "admin-alerts"
    msg: "I'm done"
    attrs:
       tags: [ heavy_check_mark ]
       priority: 4
'''
import json

from ansible.errors import AnsibleError, AnsibleActionFail, AnsibleActionSkip
from ansible.plugins.action import ActionBase
from ansible.module_utils.six import string_types
from ansible.module_utils.urls import open_url
from ansible.module_utils._text import to_text

# Load the display handler to send logging to CLI or relevant display mechanism
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class ActionModule(ActionBase):

    BYPASS_HOST_LOOP = False       # if True, runs once per play
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        
        err = None

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        url = self._task.args.get('url', 'https://ntfy.sh')
        if not isinstance(url, string_types):
            err = "Invalid type supplied for url option, it must be a string"

        # get topic from argument to module or from play vars
        topic = self._task.args.get('topic', task_vars.get('topic', 'test-topic'))
        msg   = self._task.args.get('msg', "Ansible playbook")
        attrs   = self._task.args.get('attrs', None)

        if not isinstance(topic, string_types):
            err = "Invalid type supplied for topic option, it must be a string"

        if err:
            raise AnsibleActionFail(err)

        display.vv("ntfy: notifying topic [%s] at [%s]" % (topic, url))

        # We POST JSON so prepare the data and append attributes if existent
        data = {
            "topic"     : topic,
            "message"   : msg,
        }
        if attrs is not None:
            data.update(attrs)

        resp = open_url(url,
                    data=json.dumps(data),
                    method='POST',
                    http_agent="Ansible/ntfy")

        # {"id":"xvimLyRhdF2B","time":1666985632,"event":"message","topic":"12","message":"that's a wrap"}

        resp_data = json.loads(to_text(resp.read()))

        result = {
            "changed": False,
            "failed": False,
            "msg": "ok",
            "url" : url,
            # I'm hiding `topic' here as it might be secret
        }
        result.update(resp_data)

        return result
