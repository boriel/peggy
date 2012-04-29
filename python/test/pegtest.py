#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from grammar import Grammar

inputText = open(sys.argv[1], 'rt').read()
print Grammar.match(inputText)

