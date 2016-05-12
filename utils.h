/* ------------------------------------------------------------------------
 *
 * utils.h
 *		prototypes of various support functions
 *
 * Copyright (c) 2016, Postgres Professional
 *
 * ------------------------------------------------------------------------
 */
#ifndef UTILS_H
#define UTILS_H

#include "postgres.h"
#include "nodes/relation.h"
#include "nodes/nodeFuncs.h"

typedef struct
{
	RelOptInfo *child;
	RelOptInfo *parent;
	int			sublevels_up;
} ReplaceVarsContext;

bool clause_contains_params(Node *clause);

int cmp_tlist_vars(const void *a, const void *b);
List * sort_rel_tlist(List *tlist);

#endif
