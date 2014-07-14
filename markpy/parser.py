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


import string
from elementnode import *
from elementstack import ElementStack

class Parser:
	""" This is the parser for the MarkSC language. It provides a static
	parseDocument method aimed to parse a MarkSC document.
	"""

	@staticmethod
	def parse_document(s):
		""" Parse a string and return the root of the resulting tree """

		def escape(ch):
			escape_list = {
				"\\$": "$",
				"\\%": "%",
				"\\+": "+",
				"\\*": "*",
				"\\!": "!",
				"\\/": "/",
				"\\\\": "\\",
			}
			
			if ch in escape_list:
				return escape_list[ch]
			else:
				return ch
		
		# Strip all trailing blanks
		s = "\n".join(map(lambda x: string.rstrip(x), s.split("\n")))
		
		_element_stack = ElementStack()
		_element_stack.push(
			DocumentNode()
		)

		chid = 0
		new_line = True
		
		while chid < len(s):
			ch = s[chid]
			
			if ch == '\\':
				chid += 1
				ch += s[chid]
			
			# dbgStr = s[chid:].replace('\n', '\\n')
			# print "DBG '", dbgStr[0: min(80, len(dbgStr))], "'"
			# print _element_stack._stack
			
			if new_line:
				new_line = False
				
				########################################################
				# Comments                                             #
				########################################################
				if ch == '#': # Comment, skip line
					chid = s.index('\n', chid) + 1
					new_line = True
					continue


				########################################################
				# Images                                               #
				########################################################
				if ch == '^':
					
					# Images are block-level elements
					_element_stack.pop(until = BlockNode)

					path = ""
					desc = ""
					
					end_of_tag = s.index('^', chid+1)
					path = s[chid+1 : end_of_tag]
					
					_element_stack.push(
						ImageNode(path = path)
					)
					_element_stack.push(
						ParagraphNode()
					)						
						
					chid = end_of_tag + 1
					
					continue


				########################################################
				# Alerts                                               #
				########################################################
				if ch == '!':  # Alert
					
					# Alerts are block-level elements
					_element_stack.pop(until = BlockNode)
					
					alert_level = 0
					while s[chid] == '!':
						alert_level += 1
						chid += 1
				
					_element_stack.push(
						AlertNode(level = alert_level)
					)
					_element_stack.push(
						ParagraphNode()
					)

					continue


				########################################################
				# Section                                              #
				########################################################				
				if ch == '=':

					title_depth = 0
					while s[chid] == '=':
						title_depth += 1
						chid += 1
					
					_element_stack.pop(until = SectionNode)
					while _element_stack.top().attrib['depth'] >= title_depth:
						_element_stack.pop()
						_element_stack.pop(until = SectionNode)
					assert title_depth - _element_stack.top().attrib['depth'] <= 1

					_element_stack.push(
						SectionNode()
					)
					_element_stack.push(
						SectionTitleNode()
					)
					_element_stack.push(
						ParagraphNode()
					)

					continue
				
				########################################################
				# Empty line                                           #
				########################################################
				elif ch == '\n':

					while s[chid] == '\n':
						chid += 1
					
					if not _element_stack.count(types = BlockNode):
						if not isinstance(_element_stack.top(), DocumentNode):
							_element_stack.pop(until = SectionNode)
							_element_stack.push(
								BlockNode()
							)
					else:
						_element_stack.pop(until = BlockNode)

					new_line = True
					continue

				########################################################
				# Paragraph continuation                               #
				########################################################				
				elif ch == '-' and s[chid+1] == '>':
					chid += 2
					continue
				
				########################################################
				# List item                                            #
				########################################################
				elif ch == '-' and s[chid+1] == ' ':
					
					if not _element_stack.count(types = ListContainerNode):
						_element_stack.pop(until = [BoxedNode, BlockNode])
						_element_stack.push(
							ListContainerNode()
						)
					else:
						_element_stack.pop(until = ListItemNode)
						_element_stack.pop()
						
					_element_stack.push(
						ListItemNode()
					)
					_element_stack.push(
						ParagraphNode()
					)

					chid += 1
					continue
					
					
				########################################################
				# Full-latex                                           #
				########################################################				
				elif (ch == '$' and s[chid+1] == '$') or (ch == '\\['):
					if not _element_stack.count(FormulaNode):
						_element_stack.pop(until = BlockNode)
						
						end_tag = '$$' if ch == '$' else '\\]'
						end_of_formula = s.index(end_tag, chid+1)
						latex = s[chid+1:end_of_formula]
						
						_element_stack.push(
							FormulaNode()
						)
						_element_stack.push(
							StringNode(string = latex)
						)
						_element_stack.pop()
						_element_stack.pop()
						
						chid = end_of_formula+len(end_tag)
					else:
						_element_stack.pop(until = BlockNode)	
					
					continue				
				
				
				########################################################
				# Code                                                 #
				########################################################
				elif ch == '~': 
					assert s[chid : chid+3] == '~~~'
					
					_element_stack.pop(until = BlockNode)
					
					end_of_code = s.index('~~~\n', chid+1)
					
					snippet = s[chid+3 : end_of_code]
					
					_element_stack.push(
						CodeNode()
					)
					_element_stack.push(
						StringNode(string = snippet)
					)
					_element_stack.pop()
					_element_stack.pop()
										
					chid = end_of_code + 4
					continue


				########################################################
				# End of block                                         #
				########################################################
				elif ch == '%': # Endblock
					
					# Pop last block
					assert _element_stack.count(types = BlockNode) > 0
					
					_element_stack.pop(until = BlockNode)
					_element_stack.pop()
					
					_element_stack.push(
						BlockNode()
					)
					
					assert( s[chid+1] == '\n')
					chid += 2
					new_line = True
					
					continue


				########################################################
				# All other chars                                      #
				########################################################				
				else:
					# After multiple \n
					if not _element_stack.count(types = ParagraphNode):
						continue
					# There is a title
					elif _element_stack.count(types = SectionTitleNode):
						_element_stack.pop(until = SectionNode)
						_element_stack.push(
							BlockNode()
						)
						continue
					else:
						raise NotImplementedError
			
			
			else: # new_line = False
				
				########################################################
				# Inline-latex                                         #
				########################################################				
				if ch == '$' or ch == '\\(':
					if not _element_stack.count(FormulaSpanNode):
						_element_stack.pop(
							until = [
								ParagraphNode,
								BoldfaceSpanNode,
								ItalicSpanNode,
								TypewriterSpanNode
							]
						)
						
						end_tag = '$' if ch == '$' else '\\)'
						end_of_formula = s.index(end_tag, chid+1)
						latex = s[chid+1:end_of_formula]
						
						_element_stack.push(
							FormulaSpanNode()
						)
						_element_stack.push(
							StringNode(string = latex)
						)
						_element_stack.pop()
						_element_stack.pop()
						
						chid = end_of_formula+len(end_tag)
						
					else:
						_element_stack.pop(
							until = [
								ParagraphNode,
								BoldfaceSpanNode,
								ItalicSpanNode,
								TypewriterSpanNode
							]
						)
						
					continue
				
				########################################################
				# Boldface span                                        #
				########################################################
				if ch == '*':
					if not _element_stack.count(BoldfaceSpanNode):
						_element_stack.pop(until = ParagraphNode)

						_element_stack.push(
							BoldfaceSpanNode()
						)
					else:
						_element_stack.pop(until = ParagraphNode)
						
					chid += 1
					continue
				
				
				########################################################
				# Italic span                                          #
				########################################################				
				elif ch == "/":
					if not _element_stack.count(ItalicSpanNode):
						_element_stack.pop(until = ParagraphNode)

						_element_stack.push(
							ItalicSpanNode()
						)
					else:
						_element_stack.pop(until = ParagraphNode)
						
						
					chid += 1
					continue
					
				########################################################
				# Typewriter span                                      #
				########################################################
				elif ch == "+": 
					if not _element_stack.count(TypewriterSpanNode):
						_element_stack.pop(until = ParagraphNode)

						_element_stack.push(
							TypewriterSpanNode()
						)
					else:
						_element_stack.pop(until = ParagraphNode)

						
					chid += 1
					continue
				
				########################################################
				# End of line                                          #
				########################################################	
				elif ch == "\n":
					new_line = True
					chid += 1
					continue
				
				########################################################
				# Any other char                                       #
				########################################################				
				else:
					
					if not _element_stack.count(types = ParagraphNode):
						_element_stack.push(
							ParagraphNode()
						)
					
					if not _element_stack.count(types = StringNode):
						_element_stack.push(
							StringNode(string = escape(ch))
						)
					else:
						assert isinstance(_element_stack.top(), StringNode)
						
						_element_stack.top().content += escape(ch)
					
					chid += 1
					continue
		
		_element_stack.pop(until = DocumentNode)
		
		_root = _element_stack.top()
		return _root
