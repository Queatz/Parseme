""" Parseme code expander\n\n
/*$ SECTION $*/
This line begins a section.\n
\n
/*$ {expression} $*/\n
This line begins a generated section.  The result of expression is iterated, or if it's not iterable (should always be an integer in this case) it is wrapped in range(), and the current iteration can be accessed as the capital variable I.\n
\n
/*$ $*/\n
This line closes a section.\n
\n
$?{expression\n
This line begins an if statement.\n
\n
$??{[expression]\n
This line begins an else[if] block.\n
\n
$?}\n
This line ends an if statement.\n
\n\n
Anywhere in a section ${expression} is replaced by the result thereof.\n
"""

import sys

class Round:
	"""A round is a pass over a section, with the specified variables.  All ${expr} appearences are replaced with the result of expr.  ${x} expands to the value of x in the round's vars.  Variables are inherited when sections begin in other sections."""
	def __init__(self, vars = None, **kwargs):
		"Takes a dict of variables or keyword arguments, which will be added to the dict if both are supplied."
		if vars is None:
			vars = dict()
		self.vars = vars
		for kwa in kwargs:
			self.vars[kwa] = kwargs[kwa]
	
	def parseLine(self, l, vars = {}, errors = None):
		ptr = 0
		rlp = 0
		while True:
			p = ptr
			ptr = l.find('${', ptr)
			if ptr < 0:
				break
			close = l.find('}', ptr)
			if(close < 0):
				if errors is not None:
					errors.append((rlp + len(l), 'Ending brace not found.'))
				return l[:ptr] + ('\n' if l[-1] == '\n' else '')
			v = None
			try:
				v = eval(l[ptr + 2:close], None, vars)
			except:
				if errors is not None:
					errors.append((rlp + ptr + 3, 'Expression ' + repr(l[ptr + 2:close]) + ' invalid.  (' + str(sys.exc_info()[1]) + ')'))
				v = ''
			else:
				v = str(v)
			l = l[:ptr] + v + l[close + 1:]
			rlp += close + 1 - ptr - len(v)
			ptr = ptr + len(v)
		return l

class Section:
	"""A section is a section in a file.  A section starts with a line containing /*$ SECTIONNAME $*/ and closes with /*$ $*/.  These lines are removed from the final output."""
	def __init__(self, name, *rounds):
		self.name = name
		self.rounds = list(rounds)
	
	class If:
		def __init__(self, v = True):
			self.valid = v
			self.found = not v
	
	def parseLines(self, file, lines, fileName = '', lineNumberStartsAt = 0, inVars = None):
		out = ''
		ifs = []
		section = None
		for ri, r in enumerate(self.rounds):
			vars = dict(r.vars)
			if inVars:
				for a in inVars:
					vars[a] = inVars[a]
			
			vars['II'] = ri
			
			ifs = []
			section = None
			sectionName = ''
			sectionGenerator = None
			sectionLines = None
			sectionLinesOffset = 0
			sectionDepthCheck = 0
			ifStartsAt = 0
			sectionStartsAt = 0
			for linenumber, line in enumerate(lines):
				sline = line.strip()
				
				# The subsection handles everything in it
				# If we're counting lines for the sub section,
				# we don't do anything and just pass the lines
				# that we've gathered when all are found.
				if sectionLines is None:
					computeIF = 0
					# End If
					if sline[:3] == '$?}':
						if not ifs:
							file.err('Warning', 'Unmatched end if found', fileName, lineNumberStartsAt + linenumber)
						else:
							ifs.pop()
						continue
				
					# If
					elif sline[:3] == '$?{':
						ifs.append(self.If(True if not ifs else ifs[-1].valid))
					
						if ifs[-1].valid:
							computeIF = 3
						else:
							continue
				
					# Else If
					elif sline[:4] == '$??{':
						if not ifs:
							file.err('Warning', 'Heady else if found', fileName, lineNumberStartsAt + linenumber)
						else:
							if not ifs[-1].found:
								# If not matched yet
								computeIF = 4
							else:
								ifs[-1].valid = False
								continue
					
					if computeIF:
						inifis = False
						if len(sline[computeIF:]) < 1:
							inifis = True
						else:
							try:
								inifis = bool(eval(sline[computeIF:], None, vars))
							except:
								file.err('Warning', 'Invalid if expression ' + repr(sline[computeIF:]) + ', assuming false.  ' + '(' + str(sys.exc_info()[1]) + ')', fileName, lineNumberStartsAt + linenumber)
								inifis = False
				
						ifs[-1].valid = inifis
						ifs[-1].found = inifis
						
						if ifs[-1].valid:
							ifStartsAt = linenumber
					
						continue
				
				if not ifs or ifs[-1].valid:
					# Sections
					
					# End Section
					if sline[:7] == '/*$ $*/':
						if sectionDepthCheck > 0:
							sectionDepthCheck -= 1
						else:
							if section is None:
								file.err('Warning', 'Unmatched section end found.', fileName, linenumber + 1)
							elif section is True:
								out += Section(None, *(Round({'I': ri}) for ri in sectionGenerator)).parseLines(file, sectionLines, fileName, lineNumberStartsAt + sectionLinesOffset, vars)
							elif section in file.sections:
								out += file.sections[section].parseLines(file, sectionLines, fileName, lineNumberStartsAt + sectionLinesOffset, vars)
							section = None
							sectionLines = None
							sectionGenerator = None
							continue

					# Begin Section
					elif sline[:4] == '/*$ ' and sline[-4:] == ' $*/':
						if section is not None:
							sectionDepthCheck += 1
						else:
							newsection = sline[4:-4]
							
							sectionGenerator = None
							
							if newsection[0] == '{' and newsection[-1] == '}':
								try:
									sectionGenerator = eval(newsection[1:-1], None, vars)
									if not hasattr(sectionGenerator, '__iter__'):
										sectionGenerator = range(sectionGenerator)
									section = True
								except:
									section = False
									file.err('Warning', 'Invalid section expression ' + repr(newsection[1:-1]) + ', truncating section.  ' + '(' + str(sys.exc_info()[1]) + ')', fileName, lineNumberStartsAt + linenumber)
							else:
								if newsection not in file.sections:
									file.err('Warning', 'Unknown section found \'' + newsection + '\', truncating.', fileName, lineNumberStartsAt + linenumber)
								section = newsection
							
							sectionName = newsection
							sectionLinesOffset = linenumber + 1
							sectionLines = []
							sectionStartsAt = linenumber
							sectionDepthCheck = 0

							continue
					
					# Normal lines
					if sectionLines is not None:
						sectionLines.append(line)
					else:
						errors = []
						out += r.parseLine(line, vars, errors)
						for err in errors:
							file.err('Warning', 'Parse error: ' + err[1], fileName, lineNumberStartsAt + linenumber, err[0])

		if section is not None:
			file.err('Warning', 'EOF in section: ' + sectionName, fileName, lineNumberStartsAt + sectionStartsAt)
			# run section anyway?
		
		if ifs:
			file.err('Warning', 'EOF in if', fileName, lineNumberStartsAt + ifStartsAt)
			
		
		return out
			
	
	def add(self, r):
		self.rounds.append(r)

class Project:
	"""A class to hold definitions for a project.  Typically this looks like:\nProject(Section('SECTION', Round(a = 1))).parse('file.parseme.c')"""
	
	class Errors:
		def __init__(self):
			self.shown = []
		def __call__(self, type = None, message = None, file = None, line = None, char = None):
			if message is None:
				type, message = message, type
			e = (type, message, file, line, char)
			if e not in self.shown:
				typestr = (type + ' ' if type is not None else '')
				atstr = ('(' + file + (':' + str(line + 1) + (':' + str(char) if char is not None else '') if line is not None else '') + ')' if file is not None else '')
				print('Parseme: ' + typestr + atstr + (': ' if typestr or atstr else '') + message)
				self.shown.append(e)
		def clear(self):
			self.shown = []
	
	def __init__(self, *sections):
		self.sections = {}
		for s in sections:
			self.sections[s.name] = s
		self.err = self.Errors()
	
	def add(self, s):
		"Adds a section to be parsed where found in the source."
		if not s.name:
			raise Warning('Cannot add unnamed section.')
		self.sections[s.name] = s
	
	def parseOne(self, f, default = None):
		"Parses the given files.  If the keyword argument 'default' is given, that Section will be used as a base for the files."
		if f.find('.parseme') < 0:
			self.err('Fatal', 'Parseme files need to contain \'.parseme\' in their names.  The parsed file has the same name without the \'.parseme\'.', f)
			return False
		parseme = open(f, 'r')
		lines = list(parseme)
		parseme.close()
		
		if default:
			parseoutdude = default.parseLines(self, lines, f)
		else:
			parseoutdude = Section(None, Round()).parseLines(self, lines, f)
		
		outfile = open(f.replace('.parseme', '', 1), 'w')
		outfile.write(parseoutdude)
		outfile.close()
		self.err('Parsed ' + f + '...')
		return True
	
	def parse(self, *files, default = None):
		"Writes out the new parsed files.  If you supply a Section in the first argument each file will be as if it were in that section."
		errors = 0
		for f in files:
			if not self.parseOne(f, default):
				errors += 1
		return errors
