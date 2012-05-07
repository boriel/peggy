#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

from stream import Stream

# Constant for getting "Undefined" values
Undefined = object()


class Memo(object):
    ''' A memoizing table object. Returns Undefined if the object does not
    exist in the dictionary
    '''
    def __init__(self, inputSeq):
        ''' Initialize with an input Seq or sequence object object
        '''
        self.seq = inputSeq if isinstance(inputSeq, InputSeq) else InputSeq(inputSeq)
        self.memo = {}

    def __call__(self, symbol, pos):
        return self.memo.get((symbol, pos), Undefined)

    def __getitem__(self, k):
        return self.memo.get(k, Undefined)

    def __setitem__(self, k, val):
        self.memo[k] = val


class InputSeq(object):
    ''' Stores the input text, and the current position.
    Also contains a shared look up table for memoization.
    '''
    def __init__(self, inputSeq, pos = 0):
        self.inputSeq = inputSeq
        self.pos = pos
        self.memo = Memo(self)

    def __getitem__(self, k):
        return self.inputSeq[k]

    def __len__(self):
        return len(self.inputSeq)


class YYtext(object):
    ''' This class stores a recognized yytext,
    and a position where it was recognized in the input.
    '''
    def __init__(self, symbol, pos, text, name = None):
        self.symbol = symbol # Symbol Instance which create this module
        self.yytext = text
        self.pos = pos
        self.child = []
        self.name = name if name is not None else symbol.__class__.name

    def __str__(self):
        return self.yytext + ''.join(str(x) for x in self.child)

    def __len__(self):
        return len(self.yytext) + sum(len(x) for x in self.child)

    def __add__(self, other):
        if self.pos + len(self) != other.pos:
            return Undefined

        result = YYtext(self.symbol, self.pos, self.yytext, name = self.name)
        result.child = self.child + [other]
        return result

    def flatten(self):
        ''' Returns an copy of this object, flattened.
        '''
        return YYtext(self.symbol, self.pos, str(self), name = self.name)

    def __call__(self):
        ''' Returns the this YYtext evaluated through a rule action
        defined in the PEG object. If not defined, the default is the
        string representation of the matched input.
        '''
        if self.symbol.action is None:
            return str(self)

        return self.symbol.action(self)


class YYignore(YYtext):
    ''' As above, but returns '' for str method.
    Useful for discarding matches.
    '''
    def __init__(self, symbol, pos, text, ignored, name = None):
        YYtext.__init__(self, symbol, pos, text, name)
        self.ignored = ignored 

    def __str__(self):
        return ''


class Symbol(object): 
    ''' Empty / Epsilon symbol
    '''
    instr = False
    __name = None
    action = None

    def __get_name(self):
        if self.__name is None:
            return self.__class__.__name__
        return self.__name

    def __set_name(self, value):
        self.__name = value

    name = property(__get_name, __set_name)

    def __init__(self):
        self.symbol = None
    
    def parse(self, inputSequence, pos):
        return YYtext(self, pos, '', name = name) if self.symbol is None else self.symbol.parse(inputSequence, pos)

    def match(self, inputSequence, pos = None):
        ''' Tries first to get the memoized value in the table entry.
        If not found, recursively calls the symbol.parse() method.
        '''
        if not isinstance(inputSequence, InputSeq):
            inputSequence = InputSeq(inputSequence)

        if pos is None:
            pos = inputSequence.pos

        result = inputSequence.memo(self, pos)
        if result is Undefined:
            result = self.parse(inputSequence, pos)
            inputSequence.memo[(self, pos)] = result
        return result

    def __str__(self):
        ''' Returns a string (recursive) representation
        of the object avoiding reentrance.
        '''
        if self.instr:
            return self.name

        self.instr = True
        result = '' if self.symbol is None else self.toStr()
        self.instr = False
        return result

    def toStr(self):
        return ''

    @classmethod
    def symbol(cls, obj):
        ''' Converts strings to symbols, otherwise return them
        as they are.
        '''
        if isinstance(obj, str) or isinstance(obj, unicode):
            return String(obj)

        if isinstance(obj, tuple):
            return Sequence(*obj)

        return obj

    def __or__(self, other):
        return Choice(self, Symbol.symbol(other))

    def __not__(self):
        return Not(self)

    def __invert__(self):
        return Not(self)

    def __repr__(self):
        return str(self)

    def __mul__(self, other):
        return Sequence(Star(self), Symbol.symbol(other))

    def __rmul__(self, other):
        return Sequence(Star(Symbol.symbol(other)), self)

    def __add__(self, other):
        return Sequence(Plus(self), Symbol.symbol(other))



class String(Symbol):
    ''' Matches a string from a given input.
    On success returns a YYtext Symbol.
    On failure returns None.
    '''
    def __init__(self, pattern):
        self.pattern = pattern # The string to be recognized
        self.length = len(pattern)

    
    def parse(self, inputSequence, pos):
        ''' Returns an YYtext Symbol if the string can be parsed from
        the input, at the given position. Returns None otherwise.
        '''
        if len(inputSequence[pos:]) < len(self.pattern):
            return None

        if inputSequence[pos:pos + self.length] != self.pattern:
            return None

        return YYtext(self, pos, self.pattern, self.name)

    def __str__(self):
        return self.toStr()
    
    def toStr(self):
        return "'" + self.pattern + "'"


class Regexp(Symbol):
    ''' Matches the given string as a regular expression.
    '''
    def __init__(self, pattern):
        self.pattern = pattern # The string to be recognized
        self.symbol = re.compile(self.pattern)

    def parse(self, inputSequence, pos):
        ''' Returns an YYtext Symbol if al the regexp is matched
        at the given position. None otherwise.
        '''
        match = self.symbol.match(inputSequence[pos:])
        if match is not None:
            return YYtext(self, pos, match.group(), name = self.name)

    def toStr(self):
        return '/' + self.pattern + '/'



class Sequence(Symbol):
    ''' Matches all given Symbols or none
    '''
    def __init__(self, *symbols):
        ''' Init with Sequence(symbol1, symbol2, symbol3...)
        '''
        self.symbol = [Symbol.symbol(x) for x in symbols]

    def parse(self, inputSequence, pos):
        ''' Returns an YYtext Symbol if all the objects are matched in the 
        given sequence from the input, at the given position.
        Returns None otherwise.
        '''
        result = YYtext(self, pos, '')
        for symbol in self.symbol: 
            tmp = symbol.match(inputSequence, pos + len(result))
            if tmp is None:
                return None

            result += tmp;

        return result

    def toStr(self):
        return '(' + ' '.join(str(x) for x in self.symbol) + ')'
        
        
        
class Star(Symbol):   
    ''' Matches 0 or more symbols ocurrences
    '''
    def __init__(self, symbol):
        self.symbol = Symbol.symbol(symbol)

    def parse(self, inputSequence, pos):
        ''' Returns ALWAYS an YYtext Symbol, which matches greedely
        as much input as possible.
        '''
        result = YYtext(self, pos, '')
        tmp = self.symbol.match(inputSequence, pos)
        while tmp is not None and len(tmp):
            result += tmp
            tmp = self.symbol.match(inputSequence, pos + len(result))

        return result

    def toStr(self):
        return str(self.symbol) + '*'



class Plus(Symbol):
    ''' Matches 1 or more symbol occurrences
    '''
    def __init__(self, symbol):
        symbol = Symbol.symbol(symbol)
        self.symbol = Sequence(symbol, Star(symbol))
        self.originalSymbol = symbol

    def parse(self, inputSequence, pos):
        return self.symbol.match(inputSequence, pos)

    def toStr(self):
        return str(self.originalSymbol) + '+'



class Choice(Sequence):
    ''' Returns the 1st symbol that matches, None otherwise
    '''
    def parse(self, inputSequence, pos):
        for symbol in self.symbol:
            tmp = symbol.match(inputSequence, pos)
            if tmp is not None:
                break
        
        if tmp is not None:
            tmp = YYtext(self, pos, '') + tmp
        return tmp

    def toStr(self):
        return '(' + '|'.join(str(x) for x in self.symbol) + ')'



class Optional(Symbol):
    ''' Matches 0 or 1 symbol
    '''
    def __init__(self, symbol):
        self.symbol = Choice(symbol, String(''))

    def parse(self, inputSequence, pos):
        return self.symbol.match(inputSequence, pos)

    def toStr(self):
        return str(self.symbol.symbol[0]) + '?'



class And(Symbol):
    ''' Returns '' if match. None otherwise.
    '''
    def __init__(self, symbol):
        self.symbol = Symbol.symbol(symbol)

    def parse(self, inputSequence, pos):
        tmp = self.symbol.match(inputSequence, pos)
        return None if tmp is None else YYtext(self, pos, '', name = self.name)

    def toStr(self):
        return '&' + str(self.symbol)



class Not(Symbol):
    ''' Returns '' if no match. None otherwise.
    '''
    def __init__(self, symbol):
        self.symbol = Symbol.symbol(symbol)

    def parse(self, inputSequence, pos):
        tmp = self.symbol.match(inputSequence, pos)
        return None if tmp is not None else YYtext(self, pos, '', name = self.name)

    def toStr(self):
        return '!' + str(self.symbol)


class Dot(Symbol):
    ''' Returns any char, or None if EOF
    '''
    def parse(self, inputSequence, pos):
        if pos == len(inputSequence):
            return None

        return YYtext(self, pos, inputSequence[pos], name = self.name)

    def toStr(self):
        return str(self)

    def __str__(self):
        return '.'


class Range(Regexp):
    ''' Returns if a char is in the range of a, b.
    If b is not specified, then the range will be a, a
    '''
    def __init__(self, a, b = None):
        if b is None:
            b = a
        self.a = a
        self.b = b
        Regexp.__init__(self, '[' + a + '-' + b + ']')


class Ignore(Symbol):
    ''' Matches the given input, and ignores it.
    Useful for Spaces, delimiters, separators, comments, etc.
    '''
    def __init__(self, x):
        self.symbol = Symbol.symbol(x)

    def parse(self, inputSequence, pos):
        result = self.symbol.parse(inputSequence, pos)
        if result is not None:
            result = YYignore(self, pos, str(result), result, name = self.name)

        return result

    def toStr(self):
        return ''



if __name__ == '__main__':
    S = String('333')
    print S.match('33335', 0)
    print S.match('33335', 1)
    print S.match('33335', 2)
    
    S = Sequence(String('33'), String('335'))
    print S.match('33335', 0)
    
    S = Star(String('3'))
    print S.match('43335', 0)
    
    S = Sequence(Star(String('3')), String('5'))
    print S.match('33335', 0)
    
    S = Plus(String('3'))
    print S.match('33335', 0)
    print S.match('43335', 0)
    
    S = Choice(String('3'), String('4'))
    print S.match('33335', 0)
    print S.match('43335', 0)
    
    S = Star(Choice(String('3'), String('4')))
    print S.match('3343435', 0)
    
    S = Optional(String('4'))
    print S.match('3343435', 0)
    S = Optional(String('33'))
    print S.match('3343435', 0)
    
    i = InputSeq('aaabbababbbbbbbababba')
    S = Star(Choice(String('a'), String('b')))
    print S
    print S.match(i, 0)
    print S.match(i, 0)

    S = Sequence(Star(Choice(String('a'), String('b'))), String('c'))
    i = InputSeq('aaabbababbbbbbbababba')
    print S, S.match(i, 0)

    S = Star(Not(String('b')))
    print S, S.match(i, 0)

    print Star(Sequence(Not(String('b')), String('a'))).match(i, 0) # (!b a)*
    print Star(Sequence(~String('b'), String('a'))) # !('a')*
    print Sequence(Star(String('a')), String('a')).match('aaa', 0) # a*a will always fail

    number = Plus(Choice(String('0'), String('1')))  # number <- (0|1)+
    mult = Sequence(number, Star(Sequence(String('*') | String('/'), number))) # mult <- number ('*'|'/' number)*
    plus = Sequence(mult, Star(Sequence(String('+') | String('-'), mult))) # plus <- number ('+'|'-' mult)*
    expr = Sequence('(', plus, ')') | plus

    print expr
    print expr.match('(1101/11+111001-0100*10011)',0)
    print expr.match('1101/11+111001-0100*10011',0)

    # Left recursive grammar for expr with [01] numbers
    factor = Sequence(number, '*', number) | Sequence(number, '/', number) | number
    factor.name = 'factor'
    factor.symbol[0].symbol[0].symbol[2] = factor
    factor.symbol[0].symbol[1].symbol[2] = factor

    expr = Sequence(factor, '-', factor) | Sequence(factor, '+', factor) | factor
    expr.name = 'expr'
    expr.symbol[0].symbol[0].symbol[2] = expr
    expr.symbol[0].symbol[1].symbol[2] = expr
    print expr
    print expr.match('111001+01001-111+010101*1110-111',0)
    y = expr.match('111001+01001-111+010101*1110-111',0)
    print y.yytext, list(str(x) for x in y.child)

    print ~Sequence('a', 'b') | String('a') | 'b' | 'c'
    print String('a')* 'b', (String('a')* 'b').match('aaaab')
    print String('a')+ 'b', (String('a')+ 'b').match('aaaab')

    print Regexp('.Ab+'), Regexp('.Ab+').match('BAbb')
    print Dot().match('aaa')
    print Not(Dot()).match('a')

    print Range('a', 'c'), Range('a', 'c').match('b')
    print Not(('a', 'b', 'c'))
    print String('a') * ('a', 'b', 'c')
    print ('a', 'b', 'c') * String('a')
