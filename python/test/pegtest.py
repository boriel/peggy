#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from peggy import Grammar

inputText = open(sys.argv[1], 'rt').read()
print Grammar.match(inputText)

