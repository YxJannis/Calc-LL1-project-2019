# Calc-LL1-project-2019
Note: The general notion of Calc-LL(1)-Languages was later renamed to Calc-Context-Free Languages.
These are the main implementations developed for the research on Calc-LL(1) languages and a Calc-LL(1) parser in the winter semester of 2018/2019 at Bauhaus Universität Weimar.

Netstring parser
  * parses netstrings using the calc-ll(1) principle of evaluating length prefix correctness
  * underlying basic python parser structure and lexer code by Eli Bendersky (
    https://github.com/eliben/code-for-blog/blob/master/2009/py_rd_parser_example/rd_parser_bnf.py)
    
Split parse table generator
  * creates a parse table for a given grammar using first and follow sets
  * splits the parse table at the non-terminal where the Calc-LL(1) condition has to be evaluated
