/* ------------------------------------------------------------------------
 *
 * relation_info.h
 *		Data structures describing partitioned relations
 *
 * Copyright (c) 2016, Postgres Professional
 *
 * ------------------------------------------------------------------------
 */

#ifndef RELATION_INFO_H
#define RELATION_INFO_H


#include "utils.h"

#include "postgres.h"
#include "access/attnum.h"
#include "access/sysattr.h"
#include "fmgr.h"
#include "nodes/bitmapset.h"
#include "nodes/nodes.h"
#include "nodes/memnodes.h"
#include "nodes/primnodes.h"
#include "nodes/value.h"
#include "port/atomics.h"
#include "rewrite/rewriteManip.h"
#include "storage/lock.h"
#include "utils/datum.h"
#include "utils/lsyscache.h"
#include "utils/relcache.h"


/* Range bound */
typedef struct
{
	Datum	value;				/* actual value if not infinite */
	int8	is_infinite;		/* -inf | +inf | finite */
} Bound;


#define FINITE					(  0 )
#define PLUS_INFINITY			( +1 )
#define MINUS_INFINITY			( -1 )

#define IsInfinite(i)			( (i)->is_infinite != FINITE )
#define IsPlusInfinity(i)		( (i)->is_infinite == PLUS_INFINITY )
#define IsMinusInfinity(i)		( (i)->is_infinite == MINUS_INFINITY )

static inline Bound
CopyBound(const Bound *src, bool byval, int typlen)
{
	Bound bound = {
		IsInfinite(src) ?
			src->value :
			datumCopy(src->value, byval, typlen),
		src->is_infinite
	};

	return bound;
}

static inline Bound
MakeBound(Datum value)
{
	Bound bound = { value, FINITE };

	return bound;
}

static inline Bound
MakeBoundInf(int8 infinity_type)
{
	Bound bound = { (Datum) 0, infinity_type };

	return bound;
}

static inline Datum
BoundGetValue(const Bound *bound)
{
	Assert(!IsInfinite(bound));

	return bound->value;
}

static inline void
FreeBound(Bound *bound, bool byval)
{
	if (!IsInfinite(bound) && !byval)
		pfree(DatumGetPointer(BoundGetValue(bound)));
}

static inline char *
BoundToCString(const Bound *bound, Oid value_type)
{
	return IsInfinite(bound) ?
			pstrdup("NULL") :
			datum_to_cstring(bound->value, value_type);
}

static inline int
cmp_bounds(FmgrInfo *cmp_func,
		   const Oid collid,
		   const Bound *b1,
		   const Bound *b2)
{
	if (IsMinusInfinity(b1) || IsPlusInfinity(b2))
		return -1;

	if (IsMinusInfinity(b2) || IsPlusInfinity(b1))
		return 1;

	Assert(cmp_func);

	return DatumGetInt32(FunctionCall2Coll(cmp_func,
										   collid,
										   BoundGetValue(b1),
										   BoundGetValue(b2)));
}


/* Partitioning type */
typedef enum
{
	PT_ANY = 0, /* for part type traits (virtual type) */
	PT_HASH,
	PT_RANGE
} PartType;

/* Child relation info for RANGE partitioning */
typedef struct
{
	Oid				child_oid;
	Bound			min,
					max;
} RangeEntry;

/*
 * PartStatusInfo
 *		Cached partitioning status of the specified relation.
 *		Allows us to quickly search for PartRelationInfo.
 */
typedef struct PartStatusInfo
{
	Oid				relid;			/* key */
	struct PartRelationInfo *prel;
} PartStatusInfo;

/*
 * PartParentInfo
 *		Cached parent of the specified partition.
 *		Allows us to quickly search for parent PartRelationInfo.
 */
typedef struct PartParentInfo
{
	Oid				child_relid;	/* key */
	Oid				parent_relid;
} PartParentInfo;

/*
 * PartBoundInfo
 *		Cached bounds of the specified partition.
 *		Allows us to deminish overhead of check constraints.
 */
typedef struct PartBoundInfo
{
	Oid				child_relid;	/* key */

	PartType		parttype;

	/* For RANGE partitions */
	Bound			range_min;
	Bound			range_max;
	bool			byval;

	/* For HASH partitions */
	uint32			part_idx;
} PartBoundInfo;

/*
 * PartRelationInfo
 *		Per-relation partitioning information.
 *		Allows us to perform partition pruning.
 */
typedef struct PartRelationInfo
{
	Oid				relid;			/* key */
	int32			refcount;		/* reference counter */
	bool			fresh;			/* is this entry fresh? */

	bool			enable_parent;	/* should plan include parent? */

	PartType		parttype;		/* partitioning type (HASH | RANGE) */

	/* Partition dispatch info */
	uint32			children_count;
	Oid			   *children;		/* Oids of child partitions */
	RangeEntry	   *ranges;			/* per-partition range entry or NULL */

	/* Partitioning expression */
	const char	   *expr_cstr;		/* original expression */
	Node		   *expr;			/* planned expression */
	List		   *expr_vars;		/* vars from expression, lazy */
	Bitmapset	   *expr_atts;		/* attnums from expression */

	/* Partitioning expression's value */
	Oid				ev_type;		/* expression type */
	int32			ev_typmod;		/* expression type modifier */
	bool			ev_byval;		/* is expression's val stored by value? */
	int16			ev_len;			/* length of the expression val's type */
	int				ev_align;		/* alignment of the expression val's type */
	Oid				ev_collid;		/* collation of the expression val */

	Oid				cmp_proc,		/* comparison fuction for 'ev_type' */
					hash_proc;		/* hash function for 'ev_type' */

	MemoryContext	mcxt;			/* memory context holding this struct */
} PartRelationInfo;

#define PART_EXPR_VARNO				( 1 )

/*
 * PartRelationInfo field access macros & functions.
 */

#define PrelParentRelid(prel)		( (prel)->relid )

#define PrelGetChildrenArray(prel)	( (prel)->children )

#define PrelGetRangesArray(prel)	( (prel)->ranges )

#define PrelChildrenCount(prel)		( (prel)->children_count )

#define PrelReferenceCount(prel)	( (prel)->refcount )

#define PrelIsFresh(prel)			( (prel)->fresh )

static inline uint32
PrelLastChild(const PartRelationInfo *prel)
{
	if (PrelChildrenCount(prel) == 0)
		elog(ERROR, "pg_pathman's cache entry for relation %u has 0 children",
			 PrelParentRelid(prel));

	return PrelChildrenCount(prel) - 1; /* last partition */
}

static inline List *
PrelExpressionColumnNames(const PartRelationInfo *prel)
{
	List   *columns = NIL;
	int		i = -1;

	while ((i = bms_next_member(prel->expr_atts, i)) >= 0)
	{
		AttrNumber	attnum = i + FirstLowInvalidHeapAttributeNumber;
		char	   *attname = get_attname(PrelParentRelid(prel), attnum);

		columns = lappend(columns, makeString(attname));
	}

	return columns;
}

static inline Node *
PrelExpressionForRelid(const PartRelationInfo *prel, Index rti)
{
	/* TODO: implement some kind of cache */
	Node *expr = copyObject(prel->expr);

	if (rti != PART_EXPR_VARNO)
		ChangeVarNodes(expr, PART_EXPR_VARNO, rti, 0);

	return expr;
}

AttrNumber *PrelExpressionAttributesMap(const PartRelationInfo *prel,
										TupleDesc source_tupdesc,
										int *map_length);


/* PartType wrappers */
static inline void
WrongPartType(PartType parttype)
{
	elog(ERROR, "Unknown partitioning type %u", parttype);
}

static inline PartType
DatumGetPartType(Datum datum)
{
	uint32 parttype = DatumGetUInt32(datum);

	if (parttype < 1 || parttype > 2)
		WrongPartType(parttype);

	return (PartType) parttype;
}

static inline char *
PartTypeToCString(PartType parttype)
{
	switch (parttype)
	{
		case PT_HASH:
			return "1";

		case PT_RANGE:
			return "2";

		default:
			WrongPartType(parttype);
			return NULL; /* keep compiler happy */
	}
}


/* Dispatch cache */
void refresh_pathman_relation_info(Oid relid);
void invalidate_pathman_relation_info(Oid relid);
void invalidate_pathman_relation_info_cache(void);
void close_pathman_relation_info(PartRelationInfo *prel);
bool has_pathman_relation_info(Oid relid);
PartRelationInfo *get_pathman_relation_info(Oid relid);

void shout_if_prel_is_invalid(const Oid parent_oid,
							  const PartRelationInfo *prel,
							  const PartType expected_part_type);

/* Bounds cache */
void forget_bounds_of_partition(Oid partition);
PartBoundInfo *get_bounds_of_partition(Oid partition, const PartRelationInfo *prel);

/* Parent cache */
void cache_parent_of_partition(Oid partition, Oid parent);
void forget_parent_of_partition(Oid partition);
Oid get_parent_of_partition(Oid partition);

/* Partitioning expression routines */
Node *parse_partitioning_expression(const Oid relid,
									const char *expr_cstr,
									char **query_string_out,
									Node **parsetree_out);

Datum cook_partitioning_expression(const Oid relid,
								   const char *expr_cstr,
								   Oid *expr_type);

char *canonicalize_partitioning_expression(const Oid relid,
										   const char *expr_cstr);

/* Partitioning expression routines */
Node *parse_partitioning_expression(const Oid relid,
									const char *expr_cstr,
									char **query_string_out,
									Node **parsetree_out);

Datum cook_partitioning_expression(const Oid relid,
								   const char *expr_cstr,
								   Oid *expr_type);

char *canonicalize_partitioning_expression(const Oid relid,
										   const char *expr_cstr);


/* Global invalidation routines */
void delay_pathman_shutdown(void);
void finish_delayed_invalidation(void);


/* For pg_pathman.enable_bounds_cache GUC */
extern bool pg_pathman_enable_bounds_cache;

void init_relation_info_static_data(void);


#endif /* RELATION_INFO_H */
