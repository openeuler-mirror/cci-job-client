#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2026-2026. All rights reserved.
# [cci-job-client] is licensed under the Mulan PSL v2.
# Description: parse_tbox_spec 模块的单元测试
#  - parse_params / get_host_files / match_host_file / get_dc_vm_testboxes
#  - build_ip_filename_map / get_available_testboxes / retry_on_request_exception
#  - apply_machines / query_apply_task / cancel_apply_task / return_machines
# 网络相关函数使用 mock requests，避免真实依赖。
# **********************************************************************************
"""

import os
import sys
import json
import tempfile
import unittest
from unittest import mock

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_LIB_DIR = os.path.join(TESTS_DIR, '..', 'src', 'lib')
sys.path.insert(0, SRC_LIB_DIR)

import requests
import yaml

import parse_tbox_spec as tbox


class TestParseParams(unittest.TestCase):
    """parse_params: 逗号分隔 k=v 字符串解析。"""

    def test_empty_string_returns_empty_dict(self):
        self.assertEqual(tbox.parse_params(''), {})

    def test_none_returns_empty_dict(self):
        self.assertEqual(tbox.parse_params(None), {})

    def test_single_pair(self):
        self.assertEqual(tbox.parse_params('type=vm'), {'type': 'vm'})

    def test_multiple_pairs(self):
        result = tbox.parse_params('type=vm,arch=aarch64,memory=8G')
        self.assertEqual(result, {'type': 'vm', 'arch': 'aarch64', 'memory': '8G'})

    def test_pairs_with_whitespace(self):
        result = tbox.parse_params(' type = vm , arch = aarch64 ')
        self.assertEqual(result, {'type': 'vm', 'arch': 'aarch64'})

    def test_pair_with_equals_in_value(self):
        # split('=', 1) 应当只切第一个等号
        self.assertEqual(tbox.parse_params('expr=a=b'), {'expr': 'a=b'})

    def test_pair_without_equals_is_ignored(self):
        # 没有 '=' 的 segment 应被忽略
        self.assertEqual(tbox.parse_params('foo,type=vm'), {'type': 'vm'})


class TestGetHostFiles(unittest.TestCase):
    """get_host_files: 列举目录下的文件并按前缀过滤。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        # 创建若干 host yaml 文件
        for name in ('vm-2p8g.yaml', 'vm-4p16g.yaml', 'dc-1.yaml', 'host-z9.yaml'):
            with open(os.path.join(self.root, name), 'w') as f:
                f.write('ip: 1.1.1.1\n')

        # 同时建一个子目录，应该被忽略（不是文件）
        os.makedirs(os.path.join(self.root, 'subdir'))

    def test_list_all_files(self):
        result = tbox.get_host_files(self.root)
        # 子目录应被过滤掉
        self.assertNotIn('subdir', result)
        self.assertCountEqual(
            result, ['vm-2p8g.yaml', 'vm-4p16g.yaml', 'dc-1.yaml', 'host-z9.yaml']
        )

    def test_list_with_prefix(self):
        result = tbox.get_host_files(self.root, prefix='vm-')
        self.assertCountEqual(result, ['vm-2p8g.yaml', 'vm-4p16g.yaml'])

    def test_list_with_prefix_dc(self):
        result = tbox.get_host_files(self.root, prefix='dc-')
        self.assertEqual(result, ['dc-1.yaml'])

    def test_list_with_non_matching_prefix(self):
        result = tbox.get_host_files(self.root, prefix='xx-')
        self.assertEqual(result, [])

    def test_nonexistent_directory_returns_empty(self):
        self.assertEqual(tbox.get_host_files('/path/does/not/exist'), [])

    def test_none_dir_uses_lab_repo_env(self):
        with mock.patch.dict(os.environ, {'LAB_REPO': self.root}, clear=False):
            result = tbox.get_host_files(None)
        # LAB_REPO 默认 hosts 子目录
        # 由于 tmp root 没有 'hosts' 子目录，应当返回 []
        self.assertEqual(result, [])


class TestMatchHostFile(unittest.TestCase):
    """match_host_file: 检查 yaml 内容是否匹配给定 params。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        self.host_file = os.path.join(self.root, 'vm-2p8g.yaml')
        with open(self.host_file, 'w') as f:
            yaml.dump({
                'ip': '172.16.1.10',
                'arch': 'aarch64',
                'model_name': 'Kunpeng-920',
                'nr_cpu': '4',
                'memory': '8G'
            }, f)

    def test_match_all(self):
        params = {'arch': 'aarch64', 'memory': '8G', 'nr_cpu': '4'}
        content = tbox.match_host_file('vm-2p8g.yaml', self.root, params)
        self.assertIsNotNone(content)
        self.assertEqual(content['ip'], '172.16.1.10')

    def test_no_match_returns_none(self):
        params = {'arch': 'x86_64'}
        self.assertIsNone(tbox.match_host_file('vm-2p8g.yaml', self.root, params))

    def test_missing_field_in_file_returns_none(self):
        params = {'does_not_exist': 'foo'}
        self.assertIsNone(tbox.match_host_file('vm-2p8g.yaml', self.root, params))

    def test_memory_value_with_g_suffix_strips_for_compare(self):
        # 文件中 '8G' 与参数中 '8' 应被识别为相等
        params = {'memory': '8'}
        self.assertIsNotNone(tbox.match_host_file('vm-2p8g.yaml', self.root, params))

    def test_memory_value_invalid_returns_none(self):
        params = {'memory': 'notanumber'}
        self.assertIsNone(tbox.match_host_file('vm-2p8g.yaml', self.root, params))

    def test_empty_params_returns_content(self):
        content = tbox.match_host_file('vm-2p8g.yaml', self.root, {})
        self.assertIsNotNone(content)
        self.assertEqual(content['arch'], 'aarch64')

    def test_non_dict_yaml_returns_none(self):
        # yaml 文件内容不是字典
        scalar_file = os.path.join(self.root, 'scalar.yaml')
        with open(scalar_file, 'w') as f:
            f.write('just-a-string\n')
        self.assertIsNone(tbox.match_host_file('scalar.yaml', self.root, {}))

    def test_file_not_found_returns_none(self):
        self.assertIsNone(
            tbox.match_host_file('does-not-exist.yaml', self.root, {})
        )


class TestGetDcVmTestboxes(unittest.TestCase):
    """get_dc_vm_testboxes: 通过 type/arch/nr_cpu/memory 过滤 vm-* 或 dc-*。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        for name, payload in [
            ('vm-2p8g.yaml', {'arch': 'aarch64', 'nr_cpu': '2', 'memory': '8G'}),
            ('vm-2p8g-x86.yaml', {'arch': 'x86_64', 'nr_cpu': '2', 'memory': '8G'}),
            ('vm-4p16g.yaml', {'arch': 'aarch64', 'nr_cpu': '4', 'memory': '16G'}),
            ('vm-x86.yaml', {'arch': 'x86_64', 'nr_cpu': '4', 'memory': '16G'}),
            ('dc-1.yaml', {'arch': 'aarch64', 'nr_cpu': '8', 'memory': '32G'}),
        ]:
            with open(os.path.join(self.root, name), 'w') as f:
                yaml.dump(payload, f)

    def test_type_vm_with_defaults(self):
        result = tbox.get_dc_vm_testboxes(self.root, params='type=vm,arch=aarch64')
        # 默认 nr_cpu=2, memory=8G → 仅 vm-2p8g 命中
        names = sorted(r['testbox'] for r in result)
        self.assertEqual(names, ['vm-2p8g.yaml'])
        self.assertTrue(all(r['type'] == 'vm' for r in result))

    def test_type_vm_with_explicit_params(self):
        result = tbox.get_dc_vm_testboxes(
            self.root, params='type=vm,arch=aarch64,nr_cpu=4,memory=16G'
        )
        names = [r['testbox'] for r in result]
        self.assertEqual(names, ['vm-4p16g.yaml'])

    def test_type_dc(self):
        result = tbox.get_dc_vm_testboxes(
            self.root, params='type=dc,arch=aarch64,nr_cpu=8,memory=32G'
        )
        names = [r['testbox'] for r in result]
        self.assertEqual(names, ['dc-1.yaml'])

    def test_unsupported_type_returns_empty(self):
        # type=hw 不在 dc/vm 范围内
        self.assertEqual(tbox.get_dc_vm_testboxes(self.root, params='type=hw'), [])

    def test_empty_type_returns_empty(self):
        # 没有 type 时直接返回空（避免被当作 hw）
        self.assertEqual(tbox.get_dc_vm_testboxes(self.root, params=''), [])


class TestBuildIpFilenameMap(unittest.TestCase):
    """build_ip_filename_map: 排除 vm-/dc- 前缀，按 ip 建立映射。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        for name, payload in [
            ('hw-z9-1.yaml', {'ip': '10.0.0.1', 'arch': 'aarch64'}),
            ('hw-z9-2.yaml', {'ip': '10.0.0.2', 'arch': 'aarch64'}),
            ('hw-x86.yaml', {'ip': '10.0.0.3', 'arch': 'x86_64'}),
            ('vm-2p8g.yaml', {'ip': '10.0.0.4', 'arch': 'aarch64'}),
            ('dc-1.yaml', {'ip': '10.0.0.5', 'arch': 'aarch64'}),
        ]:
            with open(os.path.join(self.root, name), 'w') as f:
                yaml.dump(payload, f)

    def test_excludes_vm_and_dc(self):
        result = tbox.build_ip_filename_map(self.root)
        # vm-/dc- 应被排除
        self.assertNotIn('10.0.0.4', result)
        self.assertNotIn('10.0.0.5', result)
        self.assertEqual(set(result.keys()), {'10.0.0.1', '10.0.0.2', '10.0.0.3'})

    def test_filter_by_arch(self):
        result = tbox.build_ip_filename_map(self.root, params='arch=aarch64')
        self.assertEqual(set(result.keys()), {'10.0.0.1', '10.0.0.2'})
        self.assertEqual(result['10.0.0.1'], 'hw-z9-1.yaml')

    def test_type_param_is_stripped(self):
        # type=hw 应当被移除，不参与文件字段匹配
        result = tbox.build_ip_filename_map(self.root, params='type=hw,arch=x86_64')
        self.assertEqual(result, {'10.0.0.3': 'hw-x86.yaml'})

    def test_no_match_returns_empty(self):
        result = tbox.build_ip_filename_map(self.root, params='arch=nonexistent')
        self.assertEqual(result, {})


class TestRetryDecorator(unittest.TestCase):
    """retry_on_request_exception: 失败重试，成功短路。"""

    def test_succeeds_first_try(self):
        calls = []

        @tbox.retry_on_request_exception
        def fn():
            calls.append(1)
            return 'ok'

        self.assertEqual(fn(), 'ok')
        self.assertEqual(len(calls), 1)

    def test_retries_then_succeeds(self):
        calls = []

        @tbox.retry_on_request_exception
        def fn():
            calls.append(1)
            if len(calls) < 3:
                raise requests.exceptions.ConnectionError('fail')
            return 'ok'

        with mock.patch('time.sleep', return_value=None):
            self.assertEqual(fn(), 'ok')
        self.assertEqual(len(calls), 3)

    def test_raises_last_exception_after_max_retries(self):
        calls = []

        @tbox.retry_on_request_exception
        def fn():
            calls.append(1)
            raise requests.exceptions.Timeout('boom')

        with mock.patch('time.sleep', return_value=None):
            with self.assertRaises(requests.exceptions.Timeout):
                fn()
        self.assertEqual(len(calls), tbox.MAX_RETRIES)


def _make_mock_response(json_data, status_code=200):
    """构造一个 mock 的 requests.Response 对象。"""
    mock_resp = mock.Mock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.content = json.dumps(json_data).encode()
    mock_resp.raise_for_status.return_value = None
    return mock_resp


class TestApplyMachines(unittest.TestCase):
    """apply_machines: POST /machines/apply。"""

    def test_success_returns_task_id(self):
        with mock.patch.object(
            tbox.requests, 'post',
            return_value=_make_mock_response({'status': 200, 'data': 42})
        ) as post:
            task_id = tbox.apply_machines(
                ip_list=['1.1.1.1'],
                duration=3600,
                api_key='k',
                api_url='http://example.com/api/v1/ops'
            )
        self.assertEqual(task_id, 42)
        # 验证请求体
        called_args, called_kwargs = post.call_args
        self.assertEqual(called_kwargs['json']['ips'], ['1.1.1.1'])
        self.assertEqual(called_kwargs['json']['duration'], '3600s')
        self.assertEqual(called_kwargs['headers']['x-api-key'], 'k')

    def test_api_error_raises_value_error(self):
        with mock.patch.object(
            tbox.requests, 'post',
            return_value=_make_mock_response({'status': 500, 'error': 'oops'})
        ):
            with self.assertRaises(ValueError):
                tbox.apply_machines(['1.1.1.1'], 60, 'k',
                                 api_url='http://example.com/api/v1/ops')


class TestQueryApplyTask(unittest.TestCase):
    """query_apply_task: GET /machines/apply/{id}。"""

    def test_success(self):
        with mock.patch.object(
            tbox.requests, 'get',
            return_value=_make_mock_response({'status': 200, 'data': {'state': 'completed'}})
        ) as get_mock:
            data = tbox.query_apply_task(7, 'k', api_url='http://x/api/v1/ops')
        self.assertEqual(data, {'state': 'completed'})
        # URL 中应当包含 task_id
        self.assertIn('/machines/apply/7', get_mock.call_args.args[0])

    def test_api_error_raises_value_error(self):
        with mock.patch.object(
            tbox.requests, 'get',
            return_value=_make_mock_response({'status': 400, 'error': 'bad'})
        ):
            with self.assertRaises(ValueError):
                tbox.query_apply_task(7, 'k', api_url='http://x/api/v1/ops')


class TestCancelApplyTask(unittest.TestCase):
    """cancel_apply_task: DELETE /machines/apply/{id}。"""

    def test_success_returns_true(self):
        with mock.patch.object(
            tbox.requests, 'delete',
            return_value=_make_mock_response({'status': 200})
        ):
            result = tbox.cancel_apply_task(7, 'k',
                                           api_url='http://x/api/v1/ops')
        self.assertTrue(result)

    def test_api_error_raises_value_error(self):
        with mock.patch.object(
            tbox.requests, 'delete',
            return_value=_make_mock_response({'status': 500, 'error': 'nope'})
        ):
            with self.assertRaises(ValueError):
                tbox.cancel_apply_task(7, 'k', api_url='http://x/api/v1/ops')


class TestReturnMachines(unittest.TestCase):
    """return_machines: POST /machines/return。"""

    def test_success(self):
        payload = {'success_list': ['1.1.1.1'], 'fail_list': []}
        with mock.patch.object(
            tbox.requests, 'post',
            return_value=_make_mock_response({'status': 200, 'data': payload})
        ) as post:
            result = tbox.return_machines(['1.1.1.1'], [1], 'k',
                                          api_url='http://x/api/v1/ops')
        self.assertEqual(result, payload)
        sent = post.call_args.kwargs['json']
        self.assertEqual(sent['ip_list'], ['1.1.1.1'])
        self.assertEqual(sent['task_ids'], [1])

    def test_api_error_raises_value_error(self):
        with mock.patch.object(
            tbox.requests, 'post',
            return_value=_make_mock_response({'status': 500, 'error': 'bad'})
        ):
            with self.assertRaises(ValueError):
                tbox.return_machines(['1.1.1.1'], [1], 'k',
                                     api_url='http://x/api/v1/ops')


class TestPollApplyTask(unittest.TestCase):
    """poll_apply_task: 轮询直到完成/失败/超时/中断。"""

    def setUp(self):
        # 屏蔽 sleep 加速测试
        self._sleep_patcher = mock.patch('time.sleep', return_value=None)
        self._sleep_patcher.start()
        self.addCleanup(self._sleep_patcher.stop)

    def test_completed_returns_ips(self):
        completed_data = {
            'state': 'completed',
            'schedule': {
                'started_tasks': [
                    {'machine': '10.0.0.1', 'state': 'complete'},
                    {'machine': '10.0.0.2', 'state': 'complete'},
                ]
            }
        }
        with mock.patch.object(tbox, 'query_apply_task',
                               return_value=completed_data):
            ips = tbox.poll_apply_task(
                task_id=1, api_key='k',
                api_url='http://x/api/v1/ops',
                poll_interval=0.01, duration=10
            )
        self.assertEqual(ips, ['10.0.0.1', '10.0.0.2'])

    def test_no_started_tasks_then_completed(self):
        # 第一次: completed 但 started_tasks 为空 → 继续轮询
        # 第二次: 真正的 completed
        data1 = {'state': 'completed', 'schedule': {'started_tasks': []}}
        data2 = {
            'state': 'completed',
            'schedule': {
                'started_tasks': [{'machine': '10.0.0.1', 'state': 'complete'}]
            }
        }
        with mock.patch.object(tbox, 'query_apply_task',
                               side_effect=[data1, data2]):
            ips = tbox.poll_apply_task(1, 'k', api_url='http://x/api/v1/ops',
                                       poll_interval=0.01, duration=10)
        self.assertEqual(ips, ['10.0.0.1'])

    def test_failed_raises_value_error(self):
        with mock.patch.object(tbox, 'query_apply_task',
                               return_value={'state': 'failed'}):
            with self.assertRaises(ValueError):
                tbox.poll_apply_task(1, 'k', api_url='http://x/api/v1/ops',
                                     poll_interval=0.01, duration=10)

    def test_canceled_raises_value_error(self):
        with mock.patch.object(tbox, 'query_apply_task',
                               return_value={'state': 'canceled'}):
            with self.assertRaises(ValueError):
                tbox.poll_apply_task(1, 'k', api_url='http://x/api/v1/ops',
                                     poll_interval=0.01, duration=10)

    def test_timeout_raises_and_cancels(self):
        # 第一次查询: pending；后续查询将被 timeout 中断
        # 由于实现先检查 elapsed > duration 再 sleep，这里让 time.time 单调递增
        fake_time = [0.0, 0.0, 100.0]
        fake_time_iter = iter(fake_time)

        def fake_time_fn():
            return next(fake_time_iter)

        with mock.patch.object(tbox, 'query_apply_task',
                               return_value={'state': 'pending'}), \
             mock.patch.object(tbox, 'cancel_apply_task',
                               return_value=True) as cancel_mock, \
             mock.patch('time.time', side_effect=fake_time_fn):
            with self.assertRaises(TimeoutError):
                tbox.poll_apply_task(1, 'k', api_url='http://x/api/v1/ops',
                                     poll_interval=0.01, duration=10)
        cancel_mock.assert_called()

    def test_query_exception_raises_value_error(self):
        with mock.patch.object(tbox, 'query_apply_task',
                               side_effect=Exception('boom')):
            with self.assertRaises(ValueError):
                tbox.poll_apply_task(1, 'k', api_url='http://x/api/v1/ops',
                                     poll_interval=0.01, duration=10)


class TestGetAvailableTestboxes(unittest.TestCase):
    """get_available_testboxes: 顶层调度入口。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        with open(os.path.join(self.root, 'vm-2p8g.yaml'), 'w') as f:
            yaml.dump({'arch': 'aarch64', 'nr_cpu': '2', 'memory': '8G'}, f)

    def test_dispatch_to_dc_vm(self):
        result = tbox.get_available_testboxes(
            self.root, params='type=vm,arch=aarch64'
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['testbox'], 'vm-2p8g.yaml')
        self.assertEqual(result[0]['type'], 'vm')

    def test_unknown_type_returns_empty(self):
        self.assertEqual(
            tbox.get_available_testboxes(self.root, params='type=unknown'),
            []
        )

    def test_hw_type_dispatches_to_hw_path(self):
        # 这里通过 mock 掉 get_hw_testboxes 验证分发
        with mock.patch.object(
            tbox, 'get_hw_testboxes',
            return_value=[{'testbox': 'hw-x.yaml', 'type': 'hw', 'task_id': 1, 'ip': '1.1.1.1'}]
        ) as hw_mock:
            result = tbox.get_available_testboxes(
                self.root, params='type=hw', api_key='k',
                api_url='http://x/api/v1/ops'
            )
        self.assertEqual(result[0]['testbox'], 'hw-x.yaml')
        hw_mock.assert_called_once()

    def test_empty_type_dispatches_to_hw(self):
        # type 为空时,代码逻辑会进入 hw 分支
        with mock.patch.object(
            tbox, 'get_hw_testboxes', return_value=[]
        ) as hw_mock:
            result = tbox.get_available_testboxes(self.root, params=None)
        self.assertEqual(result, [])
        hw_mock.assert_called_once()


class TestGetHwTestboxes(unittest.TestCase):
    """get_hw_testboxes: 申请 + 轮询 + 归还的完整流程。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name
        with open(os.path.join(self.root, 'hw-1.yaml'), 'w') as f:
            yaml.dump({'ip': '10.0.0.1', 'arch': 'aarch64'}, f)
        # 屏蔽 sleep
        self._sleep_patcher = mock.patch('time.sleep', return_value=None)
        self._sleep_patcher.start()
        self.addCleanup(self._sleep_patcher.stop)

    def test_apply_failure_raises_and_returns_machines(self):
        # apply 抛错 → get_hw_testboxes 应包装为 ValueError
        with mock.patch.object(tbox, 'apply_machines',
                               side_effect=Exception('apply boom')):
            with self.assertRaises(ValueError) as ctx:
                tbox.get_hw_testboxes(
                    dir_path=self.root,
                    params='type=hw,arch=aarch64',
                    api_key='k', api_url='http://x/api/v1/ops',
                    poll_interval=0.01, duration=10
                )
        self.assertIn('apply machines', str(ctx.exception).lower())

    def test_poll_failure_triggers_return_machines(self):
        # apply 成功, poll 抛错, 应当调用 return_machines 并重新抛出
        with mock.patch.object(tbox, 'apply_machines', return_value=99), \
             mock.patch.object(tbox, 'poll_apply_task',
                               side_effect=Exception('poll boom')), \
             mock.patch.object(tbox, 'return_machines',
                               return_value={}) as ret_mock:
            with self.assertRaises(Exception):
                tbox.get_hw_testboxes(
                    dir_path=self.root,
                    params='type=hw,arch=aarch64',
                    api_key='k', api_url='http://x/api/v1/ops',
                    poll_interval=0.01, duration=10
                )
        ret_mock.assert_called_once_with(
            ['10.0.0.1'], [99], 'k', 'http://x/api/v1/ops'
        )

    def test_success_path_returns_testbox_dicts(self):
        # 完整成功路径
        with mock.patch.object(tbox, 'apply_machines', return_value=99), \
             mock.patch.object(tbox, 'poll_apply_task',
                               return_value=['10.0.0.1']):
            result = tbox.get_hw_testboxes(
                dir_path=self.root,
                params='type=hw,arch=aarch64',
                api_key='k', api_url='http://x/api/v1/ops',
                poll_interval=0.01, duration=10
            )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['testbox'], 'hw-1.yaml')
        self.assertEqual(result[0]['type'], 'hw')
        self.assertEqual(result[0]['task_id'], 99)
        self.assertEqual(result[0]['ip'], '10.0.0.1')

    def test_no_ip_map_returns_empty(self):
        # 没有任何匹配的 ip 文件
        empty_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__('shutil').rmtree(empty_dir))
        result = tbox.get_hw_testboxes(
            dir_path=empty_dir,
            params='type=hw,arch=aarch64',
            api_key='k', api_url='http://x/api/v1/ops',
            poll_interval=0.01, duration=10
        )
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()