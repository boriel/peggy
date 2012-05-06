#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Implements PEG grammar in PEG,
# as described at http://pdos.csail.mit.edu/papers/parsing:popl04.pdf

from peg import *


EndOfFile = ~Dot()
EndOfLine = String('\r\n') | '\n' | '\r'
Space = EndOfLine | ' ' | '\t'
Comment = Sequence(String('#'), Sequence(~EndOfLine, Dot())* EndOfLine)
Spacing = Ignore(Star(Space | Comment))
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
#Expression.name = 'Expression'
Expression.symbol = [Sequence_, Star(Sequence(SLASH, Sequence_))]
Definition = Sequence(Identifier, LEFTARROW, Expression)
Grammar = Sequence(Spacing, Definition+ EndOfFile)



def Char_action(yytext):
    ''' Action for Char object
    '''
    yy = str(yytext)
    if yy == '\\t': 
        yy = '\t'
    elif yy == '\\r':
        yy = '\r'
    elif yy == '\\n':
        yy = '\n'
    elif yy == '\\\\':
        yy = '\\'
    elif yy[0] == '\\' and yy[1] >= '0' and yy[1] <= '7':
        yy = chr(int(yy[1:], 8))
    
    return yy
Char.action = Char_action


def Sequence__action(yytext):
    ''' Action for Sequence object
    '''
    return [x() for x in yytext.child]
Sequence_.action = Sequence__action



def Range__action(yytext):
    ''' Action for Range_ object
    '''
    print yytext.symbol.name
    yy = str(yytext)

    if len(yy) == 1:
        return String(yy)

    return Range(yy[0], yy[2])
Range_.action = Range__action
    


def Class_action(yytext):
    ''' Action for Class object
    '''
    tmp = [x.child[1]() for x in yytext.child[1].child[0].child]
    if len(tmp) == 1:
        return tmp[0]
    return Choice(*tuple(x for x in tmp))
Class.action = Class_action
    


q = Range_.match('a-z')
print q()
print type(q())

q = Class.match('[a-zA-Z]')
print q()
print type(q())

