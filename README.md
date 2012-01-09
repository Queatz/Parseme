Parseme
======

Use Python to expand/configure files.

Dictionary
---------

Project - A collection of files to be parsed.  
Section - A section of code to be expanded.  
Round   - A single iteration over a section with a user-defined set of variables.  

Usage
-----

If you wanted to use Parseme in a file called main.c, you would create a file called main.parseme.c, copy in the contents of main.c, and start chunking away at the code.

Parseme is not a commandline tool.  You use it in your setup scripts.  See test.py for a minimal example.

In the Code
----------

	/*$ SECTION $*/
This line begins a section called SECTION.

	/*$ {expression} $*/
This line begins a generated section.  The result of `expression` is iterated, or if it's not iterable (should always be an integer in this case) it is wrapped in range(), and the current iteration can be accessed as the capital variable `I`.

	/*$ $*/
This line closes a section.

	$?{expression
This line begins an if statement.

	$??{[expression]
This line begins an else[if] block.

	$?}
This line ends an if statement.

Anywhere in a section `${expression}` is replaced by the result thereof.
