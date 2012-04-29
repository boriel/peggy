#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Implements PEG grammar in PEG,
# as described at http://pdos.csail.mit.edu/papers/parsing:popl04.pdf

from peg import *


EndOfFile = ~Dot()
EndOfLine = String('\r\n') | '\n' | '\r'
Space = EndOfLine | ' ' | '\t'
Comment = Sequence(String('#'), Sequence(~EndOfLine, Dot())* EndOfLine)
Spacing = Star(Space | Comment)
DOT = Sequence('.', Spacing)
CLOSE = Sequence(')', Spacing)
OPEN = Sequence('(', Spacing)
PLUS = Sequence('+', Spacing)
STAR = Sequence('*', Spacing)
QUESTION = Sequence('?', Spacing)
NOT = Sequence(Choice('!', '~'), Spacing)
AND = Sequence('&', Spacing)
SLASH = Sequence(Choice('/', '|'), Spacing)
LEFTARROW = Sequence('<-', Spacing)

Char = Sequence('\\', String('n')|'r'|'t'|"'"|'"'|'['|']'|'\\') | \
    Sequence('\\', Range('0', '2'), Range('0', '7'), Range('0', '7')) | \
    Sequence('\\', Range('0', '7'), Optional(Range('0', '7'))) | \
    Sequence(Not('\\'), Dot())

Range_ = Sequence(Char, '-', Char) | Char
Class = Sequence('[', Sequence(Not(']'), Range_)* ']', Spacing)
Literal = Sequence("'", Sequence(Not("'"), Char)* "'", Spacing) | \
    Sequence('"', Sequence(Not('"'), Char)* '"', Spacing) 

IdentStart = Range('a', 'z') | Range('A', 'Z')
IdentCont = IdentStart | Range('0', '9')
Identifier = Sequence(IdentStart, IdentCont* Spacing)

Expression = Sequence(Symbol, Symbol) # Dummy Object to allow recursion
Primary = Sequence(Identifier, ~LEFTARROW) | (OPEN, Expression, CLOSE) | Literal | Class | DOT
Suffix = Sequence(Primary, Optional(QUESTION | STAR | PLUS))
Prefix = Sequence(Optional(AND | NOT), Suffix)
Sequence_ = Star(Prefix)
Expression.name = 'Expression'
Expression.symbol = [Sequence_, Star(Sequence(SLASH, Sequence_))]
Definition = Sequence(Identifier, LEFTARROW, Expression)
Grammar = Sequence(Spacing, Definition+ EndOfFile)


