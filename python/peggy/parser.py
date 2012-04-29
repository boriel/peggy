#!/usr/bin/env python
# -*- coding: utf-8 -*-

from peg import *
from grammar import Grammar


class PEGerror(Exception):
    def __init__(self, msg):
        self.message = msg

    def __str__(self):
        return self.message



class Rule(object):
    ''' A decorator class used to decorate action functions.
    (see examples)
    '''
    def __init__(self, action):
        self.rule = action.func_doc
        if self.rule is None:
            self.rule = ''

        self.peg = Grammar.match(self.rule)
        if self.peg is None:
            raise PEGerror('Invalid rule syntax at function ' + action.func_name)

        self.action = action

    def __call__(self, *args, **kwargs):
        return self.action(*args, **kwargs)




@Rule
def a(a, b, c):
    ''' Pera <- [0-9]+
    '''
    pass


a(1, 2, 3)


class Parser(object):
    ''' A PEG parser generator
    '''
    pass

