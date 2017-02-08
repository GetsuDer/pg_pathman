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


#include "postgres.h"
#include "access/attnum.h"
#include "fmgr.h"
#include "port/atomics.h"
#include "storage/lock.h"
#include "utils/datum.h"


/* Range bound */
typedef struct
{
	Datum	value;				/* Actual value if not infinite */
	uint8	is_infinite;		/* bitmask where the least significant bit
								   is indicates if the bound is infinite and
								   the second one indicates if bound
								   is negative */
} Bound;


#define BOUND_INFINITY_MASK		0x01
#define BOUND_NEGATIVE_MASK		0x02

#define FINITE					0
#define PLUS_INFINITY			(BOUND_INFINITY_MASK)
#define MINUS_INFINITY			(BOUND_INFINITY_MASK | BOUND_NEGATIVE_MASK)

#define IsInfinite(i)			((i)->is_infinite & BOUND_INFINITY_MASK)
#define IsPlusInfinity(i)		(IsInfinite(i) && !((i)->is_infinite & BOUND_NEGATIVE_MASK))
#define IsMinusInfinity(i)		(IsInfinite(i) && ((i)->is_infinite & BOUND_NEGATIVE_MASK))


inline static Bound
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

inline static Bound
MakeBound(Datum value)
{
	Bound bound = { value, FINITE };

	return bound;
}

inline static Bound
MakeBoundInf(uint8 infinity_type)
{
	Bound bound = { (Datum) 0, infinity_type };

	return bound;
}

inline static Datum
BoundGetValue(const Bound *bound)
{
	Assert(!IsInfinite(bound));

	return bound->value;
}

inline static int
cmp_bounds(FmgrInfo *cmp_func, const Bound *b1, const Bound *b2)
{
	if (IsMinusInfinity(b1) || IsPlusInfinity(b2))
		return -1;
	if (IsMinusInfinity(b2) || IsPlusInfinity(b1))
		return 1;

	Assert(cmp_func);

	return FunctionCall2(cmp_func, BoundGetValue(b1), BoundGetValue(b2));
}


/*
 * Partitioning type.
 */
typedef enum
{
	PT_INDIFFERENT = 0, /* for part type traits (virtual type) */
	PT_HASH,
	PT_RANGE
} PartType;

/*
 * Child relation info for RANGE partitioning
 */
typedef struct
{
	Oid				child_oid;
	Bound			min,
					max;
} RangeEntry;

/*
 * PartRelationInfo
 *		Per-relation partitioning information
 */
typedef struct
{
	Oid				key;			/* partitioned table's Oid */
	bool			valid;			/* is this entry valid? */
	bool			enable_parent;	/* include parent to the plan */

	uint32			children_count;
	Oid			   *children;		/* Oids of child partitions */
	RangeEntry	   *ranges;			/* per-partition range entry or NULL */

	PartType		parttype;		/* partitioning type (HASH | RANGE) */
	AttrNumber		attnum;			/* partitioned column's index */
	Oid				atttype;		/* partitioned column's type */
	int32			atttypmod;		/* partitioned column type modifier */
	bool			attbyval;		/* is partitioned column stored by value? */
	int16			attlen;			/* length of the partitioned column's type */
	int				attalign;		/* alignment of the part column's type */
	Oid				attcollid;		/* collation of the partitioned column */

	Oid				cmp_proc,		/* comparison fuction for 'atttype' */
					hash_proc;		/* hash function for 'atttype' */
} PartRelationInfo;

/*
 * RelParentInfo
 *		Cached parent of the specified partition.
 *		Allows us to quickly search for PartRelationInfo.
 */
typedef struct
{
	Oid				child_rel;		/* key */
	Oid				parent_rel;
} PartParentInfo;

/*
 * PartParentSearch
 *		Represents status of a specific cached entry.
 *		Returned by [for]get_parent_of_partition().
 */
typedef enum
{
	PPS_ENTRY_NOT_FOUND = 0,
	PPS_ENTRY_PARENT,		/* entry was found, but pg_pathman doesn't know it */
	PPS_ENTRY_PART_PARENT,	/* entry is parent and is known by pg_pathman */
	PPS_NOT_SURE			/* can't determine (not transactional state) */
} PartParentSearch;


/*
 * PartRelationInfo field access macros.
 */

#define PrelParentRelid(prel)		( (prel)->key )

#define PrelGetChildrenArray(prel)	( (prel)->children )

#define PrelGetRangesArray(prel)	( (prel)->ranges )

#define PrelChildrenCount(prel)		( (prel)->children_count )

#define PrelIsValid(prel)			( (prel) && (prel)->valid )

inline static uint32
PrelLastChild(const PartRelationInfo *prel)
{
	Assert(PrelIsValid(prel));

	if (PrelChildrenCount(prel) == 0)
		elog(ERROR, "pg_pathman's cache entry for relation %u has 0 children",
			 PrelParentRelid(prel));

	return PrelChildrenCount(prel) - 1; /* last partition */
}


const PartRelationInfo *refresh_pathman_relation_info(Oid relid,
													  PartType partitioning_type,
													  const char *part_column_name,
													  bool allow_incomplete);
void invalidate_pathman_relation_info(Oid relid, bool *found);
void remove_pathman_relation_info(Oid relid);
const PartRelationInfo *get_pathman_relation_info(Oid relid);
const PartRelationInfo *get_pathman_relation_info_after_lock(Oid relid,
															 bool unlock_if_not_found,
															 LockAcquireResult *lock_result);

void delay_pathman_shutdown(void);
void delay_invalidation_parent_rel(Oid parent);
void delay_invalidation_vague_rel(Oid vague_rel);
void finish_delayed_invalidation(void);

void cache_parent_of_partition(Oid partition, Oid parent);
Oid forget_parent_of_partition(Oid partition, PartParentSearch *status);
Oid get_parent_of_partition(Oid partition, PartParentSearch *status);

PartType DatumGetPartType(Datum datum);
char * PartTypeToCString(PartType parttype);

void shout_if_prel_is_invalid(Oid parent_oid,
							  const PartRelationInfo *prel,
							  PartType expected_part_type);


/*
 * Useful static functions for freeing memory.
 */

static inline void
FreeChildrenArray(PartRelationInfo *prel)
{
	uint32	i;

	Assert(PrelIsValid(prel));

	/* Remove relevant PartParentInfos */
	if (prel->children)
	{
		for (i = 0; i < PrelChildrenCount(prel); i++)
		{
			Oid child = prel->children[i];

			/* If it's *always been* relid's partition, free cache */
			if (PrelParentRelid(prel) == get_parent_of_partition(child, NULL))
				forget_parent_of_partition(child, NULL);
		}

		pfree(prel->children);
		prel->children = NULL;
	}
}

static inline void
FreeRangesArray(PartRelationInfo *prel)
{
	uint32	i;

	Assert(PrelIsValid(prel));

	/* Remove RangeEntries array */
	if (prel->ranges)
	{
		/* Remove persistent entries if not byVal */
		if (!prel->attbyval)
		{
			for (i = 0; i < PrelChildrenCount(prel); i++)
			{
				if (!IsInfinite(&prel->ranges[i].min))
					pfree(DatumGetPointer(BoundGetValue(&prel->ranges[i].min)));

				if (!IsInfinite(&prel->ranges[i].max))
					pfree(DatumGetPointer(BoundGetValue(&prel->ranges[i].max)));
			}
		}

		pfree(prel->ranges);
		prel->ranges = NULL;
	}
}


#endif /* RELATION_INFO_H */
