#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import inspect

from peg import *
import grammar


Definition = grammar.Spacing* grammar.Definition
def Definition_action(yytext):
    return yytext.child[-1]()
Definition.action = Definition_action


class PEGerror(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return self.message



class PEGrule(object):
    ''' A decorator class used to decorate action functions.
    (see examples)
    '''
    def __init__(self, action):
        self.rule = action.func_doc
        if self.rule is None:
            self.rule = ''

        self.peg = Definition.match(self.rule)
        if self.peg is None:
            raise PEGerror('Invalid rule syntax in function ' + action.func_name)

        self.symbol, self.PEGobject = self.peg()
        self.action = action
        print self.PEGobject
        print [type(x) for x in self.PEGobject.symbol]

    def __call__(self, *args, **kwargs):
        return self.action(*args, **kwargs)

    @property
    def symbolName(self):
        ''' Returns left part of the rule.
        '''
        return str(self.peg.child[1].child[0])

    @property
    def definition(self):
        ''' Returns right part of the rule.
        '''
        return self.peg.child[1].child[2]

    def __str__(self):
        return '%s <- %s' % (self.symbolName, self.definition)

    def match(self, inputSequence, pos = None):
        return self.PEGobject.match(inputSequence, pos)
        


class Parser(object):
    ''' A PEG parser generator
    '''
    def __init__(self):
        caller = inspect.currentframe().f_back
        symbols = {} # Left-rule symbols (a dict of lists)
        self.rules = [x[1] for x in
            inspect.getmembers(sys.modules[caller.f_globals['__name__']])
            if isinstance(x[1], PEGrule)]

        if not self.rules:
            raise PEGerror('No rules defined.')

        start = self.rules[0].symbolName # First symbol will be the start one

        for obj in self.rules:
            symbols[obj.symbolName] = symbols.get(obj.symbolName, []) + [obj]


    def __str__(self):
        return '\n'.join(x.rule.strip() for x in self.rules)


    def parse(self, inputSequence):
        pass

