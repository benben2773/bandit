#!/usr/bin/env python

import sys, logging
import ast
from bandit import result_store as b_result_store
from bandit import node_visitor as b_node_visitor
from bandit import test_set as b_test_set
from bandit import meta_ast as b_meta_ast

class BanditManager():

    scope = []
    progress = 50

    def __init__(self, test_config, debug=False):
        self.logger = self._init_logger(debug)
        self.b_ma = b_meta_ast.BanditMetaAst(self.logger)
        self.b_rs = b_result_store.BanditResultStore(self.logger)
        self.b_ts = b_test_set.BanditTestSet(self.logger, test_config)

    def get_logger(self):
        return self.logger

    def get_resultstore(self):
        return self.b_rs

    def output_results(self, lines, level):
        self.b_rs.report(scope=self.scope, lines=lines, level=level)

    def output_metaast(self):
        self.b_ma.report()

    def run_scope(self, scope):
        if scope:
            self.scope = scope
            sys.stdout.write("%s [" % len(scope))
            for i, fname in enumerate(scope):
                self.logger.debug("working on file : %s" % fname)
                if i % self.progress == 0:
                    sys.stdout.write("%s.. " % i)
                    sys.stdout.flush()
                try:
                    with open(fname, 'rU') as fdata:
                        try:
                            self._execute_ast_visitor(fname, fdata, self.b_ma, self.b_rs, self.b_ts)
                        except KeyboardInterrupt as e:
                            sys.exit(2)
                except IOError as e:
                    self.logger.error("%s" % e.strerror)
            sys.stdout.write("]\n")
            sys.stdout.flush()
        else:
            self.logger.info("no filename/s provided, working from stdin")
            try:
                self._execute_ast_visitor('STDIN', sys.stdin, self.b_ma, self.b_rs)
            except KeyboardInterrupt:
                self.logger.debug("exiting")
                sys.exit(1)

    def _execute_ast_visitor(self, fname, fdata, b_ma, b_rs, b_ts):
        if fdata != None:
            res = b_node_visitor.BanditNodeVisitor(fname, self.logger, b_ma, b_rs, b_ts)
            try:
                res.visit(ast.parse("".join(fdata.readlines())))
            except SyntaxError as e:
                self.logger.error("syntax error while parsing AST from file: %s" % fname)
                sys.exit(2)

    def _init_logger(self, debug=False):
        log_level = logging.INFO
        if debug:
            log_level = logging.DEBUG
        log_format = '[%(module)s]\t%(levelname)s\t%(message)s'
        logger = logging.getLogger()
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(handler)
        logger.debug("logging initialized")
        return logger

