#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MarkPy - github.com/obag/MarkPy
# Copyright © 2014 Gabriele Farina <gabr.farina@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


class ElementStack(object):
	""" This provides a stack designed to serve as a bridge between the raw
	MarkPy code and the resulting tree structure. While the	parser pushes and
	pops the ElementNodes corresponding to the the different parts of the
	document, ElementStack builds of the resulting tree, adding parents/
	child relationships and keeping track of the depth of each node.
	"""

	def __init__(self):
		self._stack = []
	
	def push(self, obj):
		obj.attrib['depth'] = len(self._stack)
		self._stack.append(obj)

	def top(self):
		assert len(self._stack) > 0
		return self._stack[-1]
	
	def count(self, types):
		""" Count how many (open) nodes in the stack match any of the supplied
		types
		"""

		if not isinstance(types, list):
			types = [types]

		count = 0
		for obj in self._stack:
			if obj.matches_type(types):
				count += 1
				break
		
		return count
		
	def pop(self, until = []):		
		if not isinstance(until, list):
			until = [until]

		if until == []:
			assert len(self._stack) > 0
			
			if len(self._stack) > 1:
				self._stack[-2].append_child(self._stack[-1])
			self._stack.pop()
			
		else:
			if not self.count(until):
				# Skip pop request
				return
			
			while not self.top().matches_type(until):
				self.pop()
