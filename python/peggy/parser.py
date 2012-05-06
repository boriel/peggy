#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import inspect

from peg import *
import grammar


Definition = grammar.Spacing* grammar.Definition


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

        self.action = action

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


def reflect(peg, grammar):
        return {
        'Dot': lambda : Dot(),
        'Ignore': lambda : Ignore(peg.symbol.symbol),
        'Not': lambda : Not(peg.symbol.symbol),
        'Plus' : lambda : Plus(peg.symbol.symbol),
        'Range': lambda : Range(peg.symbol.a, peg.symbol.b),
        'Sequence': lambda : Sequence(peg.symbol.symbol),
        'Star': lambda : Star(peg.symbol.symbol),
        'String': lambda : String(peg.yytext),
        }[peg.name]()


def reflection(start, grammar):
    ''' Given an YYtext object, returns the PEG object
    which parses it.
    '''
    if isinstance(grammar[start], Symbol):
        return grammar[start]

    rules = grammar[start]
    rules_ = tuple(reflect(x.definition, grammar) for x in rules)
    print rules_

    if len(rules) > 1: # More than one definition?
        grammar[start] = Choice(*rules_)
    else:
        grammar[start] = rules_[0]
        print grammar

    return grammar[start]
    


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

        for rule in self.rules: 
            print rule.definition
            print rule.peg.name

        grammar = reflection(start, symbols)
        print grammar


    def __str__(self):
        return '\n'.join(x.rule.strip() for x in self.rules)

