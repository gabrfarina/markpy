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


class ElementNode(object):
	"""	Base class that all the specific elements (such as sections,
	code blocks, pictures) extend. It provides simple and general methods to
	manage the resulting tree.
	"""

	def __init__(self, attrib = {}):
		self.attrib = attrib.copy()
		self.parent = None
		self.extra = {}
		self.children = []

	def matches_type(self, types):
		""" Returns true if this node matches any of the types supplied """

		if not isinstance(types, list):
			types = [types]

		for type in types:
			if isinstance(self, type):
				return True
		return False		

	def append_child(self, nodes):
		""" Append one or more nodes to self """

		if not isinstance(nodes, list):
			nodes = [nodes]
		self.children += nodes
		
		for child in nodes:
			child.parent = self

	def find_any(self, types = []):
		""" Performs a simple DFS in the subtree whose root is self and returns
		the first node whose type matches any of the supplied types.
		"""
		if not isinstance(types, list):
			types = [types]

		if self.matches_type(types):
			return self

		if not self.children:
			return None

		for child in self.children:
			res = child.find_any(types)
			if res:
				return res

		return None

	def filter(self, types = []):
		""" Returns a ResultForest of trees connecting all nodes whose types
		match any of the supplied types. The structure of the new trees preserve
		the original structure.

		The nodes of the result (of type ResultNode) contain references to the
		original nodes.
		"""

		class ResultForest(object):
			""" This implements a simple forest (of trees) and is used by 
			ElementNode.filter as the return type
			"""

			class ResultNode(object):
				""" Basic tree implementation. Every node in the tree maintains
				a pointer (nodePtr) to the original node in the ElementNode tree
				"""

				def __init__(self, node_ptr = None):
					self.children = []
					self.node_ptr = node_ptr

				def append_child(self, nodes):
					if not isinstance(nodes, list):
						nodes = [nodes]
					self.children += nodes
					
					for child in nodes:
						child.parent = self

			def __init__(self):
				self.trees = []

		if not isinstance(types, list):
			types = [types]

		res = ResultForest()

		this_node_matches = self.matches_type(types)

		if this_node_matches:
			res.trees += [ResultForest.ResultNode(self)]

		for child in self.children:
			sub = child.filter(types)
			if sub.trees:
				if this_node_matches:
					res.trees[0].append_child(sub.trees)
				else:
					res.trees += sub.trees

		return res

	def to_string(self, prefix = ''):
		""" Returns an ASCII version of the tree """

		s = ''
		if prefix:
			s += prefix[:-3]
			s += '  +--%s ' % ('*' if self.children else '-')
		s += '%s [%s] %s %s' % (
			self.__class__.__name__,
			hex(id(self)),
			str(self.attrib),
			str(self.extra),
		)
		s += '\n'

		for (index, child) in enumerate(self.children):
			if index + 1 == len(self.children):
				sub_prefix = prefix + '   '
			else:
				sub_prefix = prefix + '  |'

			s += child.to_string(prefix = sub_prefix)

		return s

class DocumentNode(ElementNode):
	"""This node is the root of the parsed page. There shall be only one such
	element per page, and it is the root of the tree.

	The extra dict accounts for specific directives supplited via the
	#marksc:set key value
	#marksc:setraw key value
	syntax at the beginning of the file, i.e. before the beginning of any
	section.
	"""

	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)

class SectionNode(ElementNode):
	"""This node represents a section in the document."""

	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)

class BlockNode(ElementNode):
	"""Blocks are groups of one ore more paragraphs, pictures, code snippets,
	alerts, lists and so forth. If no block break is used, the sectionNode will
	have a single block, representing its whole content, as its child.

	To forcefully end a block, write a single '%' sign (with no quotes) on a
	line.
	"""

	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)

class ParagraphNode(ElementNode):
	"""Paragraphs represent chunks of plain text. The can possibly contain spans
	of bold/italic/tt text, as well as inline latex formulas. Note that para-
	graphs can NOT be split on multiple lines, unless the paragraph continuation
	is made explicit with the '->' directive. Note that the new line character
	is not added to the content of the paragraph. 
	"""

	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)

class CodeNode(ElementNode):
	"""This node represents a code snippet. codeNode will have a rawNode as its
	child, whose content will be the actual code
	"""

	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)

class RawHTMLNode(ElementNode):
	""" This node represents rawHTML code and can be useful in those cases where
	MarkPy cannot produce the desired html code (such as a custom script or div)
	"""

	def __init__(self, string, attrib={}):
		self.content = string
		ElementNode.__init__(self, attrib)
		
class StringNode(ElementNode):
	""" This node represents standard strings, and as such it is usually a leaf
	in the tree.
	"""

	def __init__(self, string, attrib={}):
		self.content = string
		ElementNode.__init__(self, attrib)

class AlertNode(ElementNode):
	""" This node represent an alert box.

	Default attribs:
	- level: the level of the warning. This corresponds to the number of ! used.
	"""

	def __init__(self, level, attrib={}):
		attrib.update({'level': level})
		ElementNode.__init__(self, attrib)
		
class ListContainerNode(ElementNode):
	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)
		
class ListItemNode(ElementNode):
	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)
		
class BoxedNode(ElementNode):
	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)

class ImageNode(ElementNode):
	def __init__(self, path, attrib={}):
		attrib.update({'path': path})
		ElementNode.__init__(self, attrib)

class TypewriterSpanNode(ElementNode):
	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)

class FormulaSpanNode(ElementNode):
	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)

class SectionTitleNode(ElementNode):
	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)
		
class FormulaNode(ElementNode):
	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)
		
class BoldfaceSpanNode(ElementNode):
	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)
		
class ItalicSpanNode(ElementNode):
	def __init__(self, attrib={}):
		ElementNode.__init__(self, attrib)