#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2026-2026. All rights reserved.
# [cci-job-client] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# Description: parse_extra_params 函数的单元测试
# **********************************************************************************
"""

import os
import sys
import unittest

# Add src/lib to path so we can import the module under test
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_LIB_DIR = os.path.join(TESTS_DIR, '..', 'src', 'lib')
sys.path.insert(0, SRC_LIB_DIR)

from parse_params_utils import parse_extra_params


class TestParseExtraParamsNoneAndEmpty(unittest.TestCase):
    """对 None 与空入参的解析行为做校验。"""

    def test_none_input_returns_none(self):
        """传入 None 时应当直接返回 None。"""
        self.assertIsNone(parse_extra_params(None))

    def test_empty_list_returns_none(self):
        """空列表没有任何参数，应当返回 None。"""
        self.assertIsNone(parse_extra_params([]))

    def test_list_of_empty_strings_returns_none(self):
        """列表里全是空白字符串，应当返回 None。"""
        self.assertIsNone(parse_extra_params(['', '   ', '\t']))


class TestParseExtraParamsSingleArg(unittest.TestCase):
    """对单条 key=value 字符串的解析做校验。"""

    def test_single_key_value(self):
        """最简单的 key=value 形式。"""
        self.assertEqual(parse_extra_params(['key=value']), ['key=value'])

    def test_single_key_value_with_spaces_around(self):
        """key=value 两侧含空格应被去除。"""
        self.assertEqual(parse_extra_params(['  key=value  ']), ['key=value'])

    def test_single_key_value_value_contains_equals(self):
        """value 中包含 '=' 时不应被拆分（split('=', 1)）。"""
        self.assertEqual(parse_extra_params(['key=a=b']), ['key=a=b'])

    def test_value_is_empty(self):
        """value 为空字符串也属于合法键值对。"""
        self.assertEqual(parse_extra_params(['key=']), ['key='])


class TestParseExtraParamsMultipleArgs(unittest.TestCase):
    """对列表中含多条参数的情况做校验。"""

    def test_multiple_separate_args(self):
        """多个 --extra 参数，每个一条 key=value。"""
        result = parse_extra_params(['kernel=linux-5.10', 'memory=8G', 'cpu=4'])
        self.assertEqual(result, ['kernel=linux-5.10', 'memory=8G', 'cpu=4'])

    def test_multiple_args_space_separated(self):
        """单条参数里以空格分隔多个 key=value。"""
        result = parse_extra_params(['kernel=linux-5.10 memory=8G cpu=4'])
        self.assertEqual(result, ['kernel=linux-5.10', 'memory=8G', 'cpu=4'])

    def test_mixed_separate_and_space_separated(self):
        """既有独立的 --extra，也有空格分隔的 --extra。"""
        result = parse_extra_params([
            'kernel=linux-5.10',
            'memory=8G cpu=4',
        ])
        self.assertEqual(result, ['kernel=linux-5.10', 'memory=8G', 'cpu=4'])

    def test_multiple_consecutive_spaces_are_treated_as_separator(self):
        """多个连续空格视作单个分隔符（split() 默认行为）。"""
        result = parse_extra_params(['a=1   b=2'])
        self.assertEqual(result, ['a=1', 'b=2'])

    def test_tab_is_a_separator(self):
        """Python str.split() 默认会把 tab/换行等空白字符都视作分隔符。"""
        result = parse_extra_params(['a=1\tb=2'])
        self.assertEqual(result, ['a=1', 'b=2'])


class TestParseExtraParamsValueWithSpace(unittest.TestCase):
    """对 value 中含有空格（拆分后不含 '='）的情况做校验。"""

    def test_value_with_space_merged_into_previous(self):
        """第二个 token 没有 '='，应被视为前一个 value 的一部分。"""
        result = parse_extra_params(['key=value with space'])
        self.assertEqual(result, ['key=value with space'])

    def test_multi_segment_value_with_spaces(self):
        """value 跨越多个空格分隔片段时，全部拼回上一个 key。"""
        result = parse_extra_params(['desc=hello world foo bar'])
        self.assertEqual(result, ['desc=hello world foo bar'])

    def test_orphan_token_without_previous_is_dropped(self):
        """孤立的 token 既不在首个位置，前一个 result 也不是 'k=v' 形式，应当被丢弃。"""
        # 第一个 segment 无 '=', 且没有前序 key 可以合并 → 整段被丢弃
        self.assertIsNone(parse_extra_params(['orphan']))


class TestParseExtraParamsEdgeCases(unittest.TestCase):
    """边界与异常情况。"""

    def test_token_without_equals_no_previous(self):
        """首条参数不含 '='，且没有前序可合并 → 结果为 None。"""
        self.assertIsNone(parse_extra_params(['just_a_word']))

    def test_garbage_only_returns_none(self):
        """全是无法解析的字符串 → None。"""
        self.assertIsNone(parse_extra_params(['foo bar baz']))

    def test_preserves_order(self):
        """解析顺序应与原始顺序一致。"""
        result = parse_extra_params(['z=1', 'a=2', 'm=3'])
        self.assertEqual(result, ['z=1', 'a=2', 'm=3'])


if __name__ == '__main__':
    unittest.main()