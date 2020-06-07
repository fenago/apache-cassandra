Effective CQL
------------------------

In this lab, we will examine common approaches to data modeling and
interacting with data stored in Apache Cassandra. This will involve us
taking a close look at the Cassandra Query Language, otherwise known as
**CQL**. Specifically, we will cover and discuss the following topics:

-   The evolution of CQL and the role it plays in the Apache Cassandra
    universe
-   How data is structured and modeled effectively for Apache Cassandra
-   How to build primary keys that facilitate high-performing data
    models at scale
-   How CQL differs from SQL
-   CQL syntax and how to solve different types of problems using it

Once you have completed this lab, you should have an understanding
of why data models need to be built in a certain way. You should also
begin to understand known Cassandra anti-patterns and be able to spot
certain types of bad queries. This should help you to build scalable,
query-based tables and write successful CQL to interact with them.

In the parts of this lab that cover data modeling, be sure to pay
extra attention. The data model is the most important part of a
successful, high-performing Apache Cassandra cluster. It is also
extremely difficult to change your data model later on, so test early,
often, and with a significant amount of data. You do not want to realize
that you need to change your model after you have already stored
millions of rows. No amount of performance-tuning on the cluster side
can make up for a poorly-designed data model!


An overview of Cassandra data modeling
--------------------------------------

* * * * *

Understanding how Apache Cassandra organizes data under the hood is
essential to knowing how to use it properly. When examining Cassandra's
data organization, it is important to determine which version of Apache
Cassandra you are working with. Apache Cassandra 3.0 represents a
significant shift in the way data is both stored and accessed, which
warrants a discussion on the evolution of CQL.

Before we get started, let's create a keyspace for this lab's work:

```
CREATE KEYSPACE fenago_ch3 WITH replication =
 {'class': 'NetworkTopologyStrategy', 'ClockworkAngels':'1'};
```

To preface this discussion, let's create an example table. Let's assume
that we want to store data about a music playlist, including the band's
name, albums, song titles, and some additional data about the songs. The
CQL for creating that table could look like this:

```
CREATE TABLE playlist (
 band TEXT,
 album TEXT,
 song TEXT,
 running_time TEXT,
 year INT,
 PRIMARY KEY (band,album,song));
```

Now we'll add some data into that table:

```
INSERT INTO playlist (band,album,song,running_time,year)
  VALUES ('Rush','Moving Pictures','Limelight','4:20',1981);
INSERT INTO playlist (band,album,song,running_time,year)
  VALUES ('Rush','Moving Pictures','Tom Sawyer','4:34',1981);
INSERT INTO playlist (band,album,song,running_time,year)
  VALUES ('Rush','Moving Pictures','Red Barchetta','6:10',1981);
INSERT INTO playlist (band,album,song,running_time,year)
  VALUES ('Rush','2112','2112','20:34',1976);
INSERT INTO playlist (band,album,song,running_time,year)
  VALUES ('Rush','Clockwork Angels','Seven Cities of Gold','6:32',2012);
INSERT INTO playlist (band,album,song,running_time,year)
  VALUES ('Coheed and Cambria','Burning Star IV','Welcome Home','6:15',2006);
```

### Cassandra storage model for early versions up to 2.2

The original underlying storage for Apache Cassandra was based on its
use of the Thrift interface layer. If we were to look at how the
underlying data was stored in older (pre-3.0) versions of Cassandra, we
would see something similar to the following:


Figure 3.1: Demonstration of how data was stored in the older storage
engine of Apache Cassandra. Notice that the data is partitioned
(co-located) by its row key, and then each column is ordered by the
column keys.

![](https://raw.githubusercontent.com/fenago/apache-cassandra/master/images/1.jpg)

As you can see in the preceding screenshot, data is simply stored by its
row key (also known as the **partitioning key**). Within each partition,
data is stored ordered by its column keys, and finally by its (non-key)
column names. This structure was sometimes referred to as a **map of a
map**. The innermost section of the map, where the column values were
stored, was called a **cell**. Dealing with data like this proved to be
problematic and required some understanding of the Thrift API to
complete basic operations.

When CQL was introduced with Cassandra 1.2, it essentially abstracted
the Thrift model in favor of a SQL-like interface, which was more
familiar to the database development community. This abstraction brought
about the concept known as the **CQL row**. While the storage layer
still viewed from the simple perspective of partitions and column
values, CQL introduced the row construct to Cassandra, if only at a
logical level. This difference between the physical and logical models
of the Apache Cassandra storage engine was prevalent in major versions:
1.2, 2.0, 2.1, and 2.2.

#### Cassandra storage model for versions 3.0 and beyond

On the other hand, the new storage engine changes in Apache Cassandra
3.0 offer several improvements. With version 3.0 and up, stored data is
now organized like this:

![](https://raw.githubusercontent.com/fenago/apache-cassandra/master/images/2.jpg)

Figure 3.2: Demonstration of how data is stored in the new storage
engine used by Apache Cassandra 3.0 and up. While data is still
partitioned in a similar manner, rows are now first-class citizens.

 

The preceding figure shows that, while data is still partitioned
similarly to how it always was, there is a new structure present. The
row is now part of the storage engine. This allows for the data model
and the Cassandra language drivers to deal with the underlying data
similar to how the storage engine does.

### Note

An important aspect not pictured in the preceding screenshot is the fact
that each row and column value has its own timestamp.

In addition to rows becoming first-class citizens of the physical data
model, another change to the storage engine brought about a drastic
improvement. As Apache Cassandra's original data model comes from more
of a key/value approach, every row is not required to have a value for
every column in a table.

The original storage engine allowed for this by repeating the column
names and clustering keys with each column value. One way around
repeating the column data was to use the
`WITH COMPACT STORAGE` directive at the time of table
creation. However, this presented limitations around schema flexibility,
in that columns could no longer be added or removed.

### Note

Do not use the `WITH COMPACT STORAGE` directive with Apache
Cassandra version 3.0 or newer. It no longer provides any benefits, and
exists so that legacy users have an upgrade path.

With Apache Cassandra 3.0, column names and clustering keys are no
longer repeated with each column value. Depending on the data model,
this can lead to a drastic difference in the disk footprint between
Cassandra 3.0 and its prior versions.

### Note

I have seen as much as a 90% reduction in disk footprint by upgrading
from Cassandra 2.x to Cassandra 3.0 and as little as 10% to 15%. Your
experience may vary, depending on the number of columns in a table, size
of their names, and primary key definition.

 

#### Data cells

Sometimes structures for storing column values are referred to as
**cells**. Queries to Cassandra essentially return collections of cells.
Assume the following table definition for keeping track of weather
station readings:

```
CREATE TABLE weather_data_by_date (
  month BIGINT,
  day BIGINT,
  station_id UUID,
  time timestamp,
  temperature DOUBLE,
  wind_speed DOUBLE,
  PRIMARY KEY ((month,day),station_id,time));
```

In this model, the `month` and `day` keys are used
to make up a composite partition key. The clustering keys are
`station_id` and `time`. In this way, for each
partition, the number of cells will be equal to the total unique
combinations of tuples:

-   `station_id`, `time`, `temperature`
-   `station_id`, `time`, `wind_speed`

Understanding a cell comes into play when building data models. Apache
Cassandra can only support 2,000,000,000 cells per partition. When data
modelers fail to consider this, partitions can become large and
ungainly, with query times eventually getting slower. This is why data
models that allow for unbound row growth are considered to be an
anti-pattern.

### Note

The maximum of 2,000,000,000 cells per partition is a hard limit. But,
practically speaking, models that allow that many cells to be written to
a single partition will become slow long before that limit is reached.


Getting started with CQL
------------------------

* * * * *

With some quick definitions of CQL data modeling and cqlsh completed,
now we'll take a look at CQL. The basic commands for creating data
structures (keyspaces, tables, and so on) will be covered right away,
with command complexity increasing as we build more useful structures.

### Creating a keyspace

Keyspaces are analogous to the logical databases of the relational
world. A keyspace contains tables, which are usually related to each
other by application, use case, or development team. When defining a
keyspace, you also have the ability to control its replication behavior,
specifying pairs of data center names and a numeric **Replication
Factor** (**RF**).

Creating a keyspace is a simple operation and can be done like this:

```
CREATE KEYSPACE [IF NOT EXISTS] <keyspace_name>
 WITH replication =
 {'class': '<replication_strategy>',
  '<data_center_name>':'<replication_factor>'}
 AND durable_writes = <true/false>;
```

 

Here is the detailed explanation of the preceding query:

-   `keyspace_name`: Valid keyspace names must be composed of
    alphanumeric characters and underscores.
-   `replication_strategy`: Either `SimpleStrategy`
    or `NetworkTopologyStrategy`.
-   `data_center_name`: Valid only
    for `NetworkTopologyStrategy`, must be the name of a valid
    data center. If using `SimpleStrategy`, specify
    `replication_factor`.
-   `replication_factor`: A numeric value representing the
    number of replicas to write for the key with which it is paired.
-   `durable_writes`: A Boolean indicating whether writes
    should be written to the commit log. If not specified, this defaults
    to `true`.

### Note

Names for keyspaces, tables, columns, and custom structures in Apache
Cassandra must be alphanumeric. The only exception to that rule is that
an underscore (`_`) is the only valid special character that
can be used.

#### Single data center example

The following example will create the `fenago_ch3` keyspace.
When a write occurs, one replica will be written to the cluster. Writes
will also be sent to the commit log for extra durability:

```
CREATE KEYSPACE IF NOT EXISTS fenago_ch3
 WITH replication =
 {'class': 'NetworkTopologyStrategy', 'ClockworkAngels':'1'}
 AND durable_writes = true;
```

### Note

`SimpleStrategy` isn't very useful, so my advice is not to use
it. It's a good idea to get into the habit of using
`NetworkTopologyStrategy`, as that's the one that should be
used in production. `SimpleStrategy` offers no advantages over
`NetworkTopologyStrategy`, and using
`SimpleStrategy` can complicate converting into a multi-data
center environment later.

 

 

#### Multi-data center example

The following example will create the `fenago_ch3b` keyspace,
as long as it does not already exist. When a write occurs, two replicas
will be written to the `ClockworkAngels` data center, and
three will be written to the `PermanentWaves` and
`MovingPictures` data centers. Writes will also be sent to
the commit log for extra durability:

```
CREATE KEYSPACE fenago_ch3_mdc
 WITH replication = {'class': 'NetworkTopologyStrategy',
  'ClockworkAngels':'2', 'MovingPictures':'3', 'PermanentWaves':'3'}
 AND durable_writes = true;
```

Once you have created your keyspace, you can use it to avoid having to
keep typing it later. Notice that this will also change your Command
Prompt:

```
cassdba@cqlsh> use fenago_ch3 ;
cassdba@cqlsh:fenago_ch3>
```

### Creating a table

Data in Cassandra is organized into storage structures known as tables.
Some older documentation may refer to tables as column families. If
someone refers to column families, it is safe to assume that they are
referring to structures in older versions of Apache Cassandra:

```
CREATE TABLE [IF NOT EXISTS] [keyspace_name.]<table_name>
 <column_name> <column_type>,
 [additional <column_name> <column_type>,]
 PRIMARY KEY ((<partition_key>[,additional <partition_key>])[,<clustering_keys]);
[WITH <options>];
```

#### Simple table example

For a small table with simple query requirements, something like this
might be sufficient:

```
CREATE TABLE users (
 username TEXT,
 email TEXT,
 department TEXT,
 title TEXT,
 ad_groups TEXT,
 PRIMARY KEY (username));
```

 

#### Clustering key example

Let's say that we wanted to be able to offer up the same data, but to
support a query for users by department. The table definition would
change to something like this:

```
CREATE TABLE users_by_dept (
  username TEXT,
  email TEXT,
  department TEXT,
  title TEXT,
  AD_groups TEXT,
  PRIMARY KEY ((department),username))
WITH CLUSTERING ORDER BY (username ASC)
  AND COMPACTION = {'class':'LeveledCompactionStrategy',
  'sstable_size_in_mb':'200'};
```

As the preceding table will be read more than it will be written to
(users queried more often than they are added), we also designate use
of `LeveledCompactionStrategy`.

### Note

The default compaction strategy is
`SizeTieredCompactionStrategy`, which tends to favor read and
write patterns that are either even (50% read, 50% write) or more
write-heavy.

For a later example, let's write some data to that table:

```
INSERT INTO users_by_dept(department,username,title,email) VALUES ('Engineering','Dinesh','Dev Lead','dinesh@piedpiper.com');
INSERT INTO users_by_dept(department,username,title,email) VALUES ('Engineering','Gilfoyle','Sys Admin/DBA','thedarkone@piedpiper.com');
INSERT INTO users_by_dept(department,username,title,email) VALUES ('Engineering','Richard','CEO','richard@piedpiper.com');
INSERT INTO users_by_dept(department,username,title,email) VALUES ('Marketing','Erlich','CMO','erlichb@aviato.com');
INSERT INTO users_by_dept(department,username,title,email) VALUES ('Finance/HR','Jared','COO','donald@piedpiper.com');
```

 

#### Composite partition key example

Solving data model problems attributed to unbound row growth can
sometimes be done by adding another partition key. Let's assume that we
want to query security entrance logs for employees. If we were to use a
clustering key on a new column named time to one of the preceding
examples, we would be continually adding cells to each partition. So
we'll build this `PRIMARY KEY` to partition our data by
`entrance` and `day`, as well as cluster it on
`checkpoint_time` and `username`:

```
CREATE TABLE security_log (
 entrance TEXT,
 day BIGINT,
 checkpoint_time TIMESTAMP,
 username TEXT,
 email TEXT,
 department TEXT,
 title TEXT,
 PRIMARY KEY ((entrance,day),checkpoint_time,username))
WITH CLUSTERING ORDER BY (checkpoint_time DESC, username ASC)
AND default_time_to_live=2592000;
```

The preceding table will store data sorted within each partition by both
`checkpoint_time` and `username`. Note that, since
we care more about the most recent data, we have designated the
clustering on `checkpoint_time` to be in descending order.
Additionally, we'll assume we have a requirement to only keep security
log data for the last 30 days, so we'll set
`default_time_to_live` to 30 days (`2592000`
seconds).

#### Table options

There are several options that can be adjusted at table-creation time.
Most of these options are present on all tables. If they are omitted
from table creation, their default values are assumed. The following are
a few of the table options: 

-   Clustering order specifies the column(s) and direction by which the
    table data (within a partition) should be stored on disk. As
    Cassandra stores data written sequentially, it's also faster when it
    can read sequentially, so learning how to utilize clustering keys in
    your models can help with performance:

```
CLUSTERING ORDER BY (<clustering_key_name <ASC|DESC>)
```

-   This setting represents the false positive probability for the
    table's bloom filter. The value can range between `0.0`
    and `1.0`, with a recommended setting of `0.1`
    (10%):

```
bloom_filter_fp_chance = 0.1
```

-   The `caching` property dictates which caching features are
    used by this table. There are two types of caching that can be used
    by a table: **key caching** and **row caching**. Key caching is
    enabled by default. Row caching can take up larger amounts of
    resources, so it defaults to disabled or `NONE`:

```
caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'}
```

-   This property allows for the addition of `comment` or
    description for the table, assuming that it is not clear from its
    name:

```
comment = ''
```

-   This enables the table for **Change Data Capture** (**CDC**) logging
    and `cdc` defaults to `FALSE`:

```
cdc = FALSE
```

-   A map structure that allows for the configuration of the compaction
    strategy, and the properties that govern it:

```
compaction = {'class': 'org.apache.cassandra.db.compaction.LeveledCompactionStrategy'}
```

Apache Cassandra 3.0 ships with three compaction strategies:

-   `SizeTieredCompactionStrategy`: This is the default
    strategy, and works well in most scenarios, specifically write-heavy
    throughput patterns. It works by finding similarly-sized SSTable
    files and combining them once they reach a certain size. If you
    create a table without configuring compaction, it will be set to the
    following options:

```
compaction = {'class': 'org.apache.cassandra.db.compaction.SizeTieredCompactionStrategy',
 'max_threshold': '32', 'min_threshold': '4'}
```

Under these settings, a minor compaction will trigger for the table when
at least `4` (and no more than `32`) SSTables are
found to be within a calculated threshold of the average SSTable file
size.

 

-   `LeveledCompactionStrategy`: The leveled compaction
    strategy builds out SSTable files as levels, where each level is 10
    times the size of the previous level. In this way, a row can be
    guaranteed to be contained within a single SSTable file 90% of the
    time. A typical leveled `compaction` config looks like
    this:

```
compaction = {'class': 'org.apache.cassandra.db.compaction.LeveledCompactionStrategy',
 'sstable_size_in_mb': '160'}
```

Leveled `compaction` is a good idea for operational patterns
where reads are twice (or more) as frequent as writes.

-   `TimeWindowCompactionStrategy`: Time-window compaction
    builds SSTable files according to time-based buckets. Rows are then
    stored according to these (configurable) buckets. Configuration for
    time window `compaction` looks like this:

```
compaction = {'class': 'org.apache.cassandra.db.compaction.TimeWindowCompactionStrategy',
 'compaction_window_unit': 'hours', 'compaction_window_size': '24'}
```

This is especially useful for time-series data, as it allows data within
the same time period to be stored together.

### Note

Time-window compaction can greatly improve query performance (over other
strategies) for time-series data that uses **time to live** (**TTL**).
This ensures that data within a bucket is tombstoned together, and
therefore the TTL tombstones should not interfere with queries for newer
data.

### Note

`TimeWindowCompactionStrategy` is new as of Apache Cassandra
3.0, and replaces `DateTieredCompactionStrategy`, which was
shipped with Apache Cassandra 2.1 and 2.2.

```
compression = {'chunk_length_in_kb': '64', 'class': 'org.apache.cassandra.io.compress.LZ4Compressor'}
```

 

This property is another map structure that allows the compression
settings for a table to be configured. Apache Cassandra ships with three
compressor classes: `LZ4Compressor` (default),
`SnappyCompressor`, and `DeflateCompressor`. Once
the class has been specified, `chunk_length` can also be
specified. By default, a table will use `LZ4Compressor`, and
will be configured as shown here:

```
compression = {'class': 'org.apache.cassandra.io.compress.LZ4Compressor',
 'chunk_length_in_kb': '64'}
```

### Note

To disable compression,
specify `compression = {'sstable_compression': ''}`.

It should be noted that the default `chunk_length_in_kb` of
`64` is intended for write-heavy workloads.  Access patterns
that are more evenly read and write, or read-heavy may see a performance
benefit from bringing that value down to as low as four. As always, be
sure to test significant changes, like this:

```
crc_check_chance = 1.0
```

With compression enabled, this property defines the probability that the
CRC compression checksums will be verified on a read operation. The
default value is `1.0`, or 100%:

```
dclocal_read_repair_chance = 0.1
```

This property specifies the probability that a read repair will be
invoked on a read. The read repair will only be enforced within the same
(local) data center:

```
default_time_to_live = 0
```

This allows all data entered into a table to be automatically deleted
after a specified number of seconds. The default value is `0`,
which disables TTL by default. TTLs can also be set from the application
side, which will override this setting. The maximum value is
`630720000`, or 20 years.

### Note

Don't forget that TTLs also create tombstones. So, if your table employs
a TTL, be sure to account for that in your overall data modeling
approach.

```
gc_grace_seconds = 864000
```

 

 

This property specifies the amount of time (in seconds) that tombstones
in the table will persist before they are eligible for collection via
compaction. By default, this is set to `864000` seconds, or 10
days.

### Note

Remember that the 10 day default exists to give your cluster a chance to
run a repair. This is important, as all tombstones must be successfully
propagated to avoid data ghosting its way back into a result set. If you
plan to lower this value, make sure that you also increase the frequency
by which the repair is run.

```
min_index_interval & max_index_interval
```

These properties work together to determine how many entries end up in
the table's index summary (in RAM). The more entries in the partition
index, the quicker a partition can be located during an operation. The
trade-off, is that more entries equal more RAM consumed. The actual
value used is determined by how often the table is accessed. Default
values for these properties are set as follows:

```
max_index_interval = 2048
min_index_interval = 128
memtable_flush_period_in_ms = 0
```

The number of milliseconds before the table's memtables are flushed from
RAM to disk. The default is zero, effectively leaving the triggering of
memtable flushes up to the commit log and the defined value of
`memtable_cleanup_threshold`:

```
read_repair_chance = 0.0
```

Similar to `dclocal_read_repair_chance`, this setting
specifies the probability that a cross-data center read repair will be
invoked. This defaults to zero (0.0), to ensure that read repairs are
limited to a single data center at a time (and therefore less
expensive):

```
speculative_retry = '99PERCENTILE';
```

This property configures rapid read protection, in that read requests
are sent to other replicas despite their consistency requirements having
been met. This property has four possible values:

-   `ALWAYS`: Every ready sends additional read requests to
    other replicas.
-   `XPERCENTILE`: Sends additional read requests only for
    requests that are determined to be in the slowest X percentile. The
    default value for this property is `99PERCENTILE`, which
    will trigger additional replica reads for request latencies in the
    99^th^ percentile, based on past performance of reads for that
    table.
-   `XMS`: Sends additional replica reads for requests that do
    not complete within X milliseconds.
-   `NONE`: Disables this functionality.

### Data types

Apache Cassandra comes with many common types that can help you with
efficient data storage and representation. As Cassandra is written in
Java, the Cassandra data types correlate directly to Java data types:

![](https://raw.githubusercontent.com/fenago/apache-cassandra/master/images/8_1_1.jpg)

![](https://raw.githubusercontent.com/fenago/apache-cassandra/master/images/8_1_2.jpg)

#### Type conversion

One common point of consternation for many folks new to Cassandra is
converting between types. This can be done either by altering the
existing table, or coercing the results at query-time with
`CAST`. While some of the types may seem interchangeable,
issues can arise when converting between types where the target type
cannot support the amount of precision required. The following type
conversions can be done without issue:

![](https://raw.githubusercontent.com/fenago/apache-cassandra/master/images/8_2.jpg)

Some notes about CQL data type conversion:

![](https://raw.githubusercontent.com/fenago/apache-cassandra/master/images/8_3.jpg)

### The primary key

The most important part of designing your data model is how you define
the primary key of your tables. As mentioned previously in this lab,
primary keys are built at table-creation time, and have the following
options:

```
PRIMARY KEY ((<partition_key>[,additional <partition_key>])[,<clustering_keys])
```

Tables in Apache Cassandra may have (both) multiple partition and
clustering keys. As previously mentioned, the partition keys determine
which nodes are responsible for a row and its replicas. The clustering
keys determine the on-disk sort order within a partition.

 

#### Designing a primary key

When designing a primary key, Cassandra modelers should have two main
considerations:

-   Does this primary key allow for even distribution, at scale?
-   Does this primary key match the required query pattern(s), at scale?

Note that on the end of each statement is the phrase at scale. A model
that writes all of its table's data into a single partition distributes
evenly when you have a 3-node cluster. But it doesn't evenly distribute
when you scale up to a 30-node cluster. Plus, that type of model puts
your table in danger of approaching the limit of 2,000,000,000 cells per
partition. Likewise, almost any model will support high-performing
unbound queries (queries without a `WHERE` clause) when they
have 10 rows across the (aforementioned) 3-node cluster. But increase
that to 10,000,000,000 rows across 30 nodes, and watch the bad queries
start to time out.

Apache Cassandra is a great tool for supporting large amounts of data at
large scale. But simply using Cassandra for that task is not enough.
Your tables must be designed to take advantage of Cassandra’s storage
and distribution model, or trouble will quickly ensue.

##### Selecting a good partition key

So, how do we pick a partition key that distributes well at scale? 
Minding your model’s potential cardinality is the key. The cardinality
of a partition key represents the number of possible values of the key,
ranging from one to infinity.

### Note

Avoid extreme ends of cardinality. Boolean columns should not be used as
a single partition key (results in only two partitions). Likewise, you
may want to avoid UUIDs or any kind of unique identifier as a single
partition key, as its high cardinality will limit potential query
patterns.

A bad partition key is easy to spot, with proper knowledge of the
business or use case.  For instance, if I wanted to be able to query all
products found in a particular store, store would seem like a good
partition key.  However, if a retailer has 1,000,000 products, all of
which are sold in all 3 of their stores, that's obviously not going to
distribute well.

 

Let's think about a time-series model. If I'm going to keep track of
security logs for a company's employees (with multiple locations), I may
think about building a model like this:

```
CREATE TABLE security_logs_by_location (
  employee_id TEXT,
  time_in TIMESTAMP,
  location_id TEXT,
  mailstop TEXT,
  PRIMARY KEY (location_id, time_in, employee_id));
```

This will store the times that each employee enters by location. And if
I want to query by a specific location, this may work for query
requirements. The problem is that, with each write, the
`location_id` partition will get bigger and bigger.
Eventually, too many employees will check in at a certain location, and
the partition will get too big and become unable to be queried.  This is
a common Cassandra modeling anti-pattern, known as **unbound row
growth**.

### Note

Cardinality may also be an issue with `location_id`. If the
company in question has 20-50 locations, this might not be so bad. But
if it only has two, this model won’t distribute well at all. That's
where knowing and understanding the business requirements comes into
play.

To fix unbound row growth, we can apply a technique called
**bucketing**. Let's assume that we know that each building location
will only have 300 employees enter each day. That means if we could
partition our table by day, we would never have much more than 300 rows
in each partition. We can do that by introducing a day bucket into the
model, resulting in a composite partition key:

```
DROP TABLE security_logs_by_location;

CREATE TABLE security_logs_by_location (
 employee_id TEXT,
 time_in TIMESTAMP,
 location_id TEXT,
 day INT,
 mailstop TEXT,
 PRIMARY KEY ((location_id, day), time_in, employee_id));
```

### Note

Creating a compound partition key is as simple as specifying the
comma-delimited partition keys inside parentheses.

Now when I insert into this table and query it, it looks something like
this:

```
INSERT INTO security_logs_by_location (location_id,day,time_in,employee_id,mailstop)
VALUES ('MPLS2',20180723,'2018-07-23 11:04:22.432','aaronp','M266');

SELECT * FROM security_logs_by_location ;

 location_id | day      | time_in                         | employee_id | mailstop
-------------+----------+---------------------------------+-------------+----------
       MPLS2 | 20180723 | 2018-07-23 12:04:22.432000+0000 |      aaronp |     M266

(1 rows)
```

Now my application can write as many rows as it needs to, without
worrying about running into too many cells per partition. The trade-off
is that when I query this table, I'll need to specify the location and
day. But business-reporting requirements typically (in this hypothetical
use case) require querying data only for a specific day, so that will
work.

##### Selecting a good clustering key

As mentioned previously, clustering determine the on-disk sort order for
rows within a partition. But a good clustering key can also help to
ensure uniqueness among the rows. Consider the table used in the
preceding examples. This section will make more sense with more data, so
let’s start by adding a few more rows:

```
INSERT INTO security_logs_by_location (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 9:04:59.377','tejam','M266');
INSERT INTO security_logs_by_location (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 7:17:38.268','jeffb','M266');
INSERT INTO security_logs_by_location (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 7:01:18.163','sandrak','M266');
INSERT INTO security_logs_by_location (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 6:49:11.754','samb','M266');
INSERT INTO security_logs_by_location (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 7:08:24.682','johno','M261');
INSERT INTO security_logs_by_location (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 7:55:45.911','tedk','M266');
```

Now, I'll query the table for all employees entering
the `MPLS2` building between 6 AM and 10 AM, on July 23, 2018:

```
SELECT * FROM security_logs_by_location
WHERE location_id='MPLS2'
AND day=20180723 AND time_in > '2018-07-23 6:00'
AND time_in < '2018-07-23 10:00';

 location_id | day      | time_in                         | employee_id | mailstop
-------------+----------+---------------------------------+-------------+----------
       MPLS2 | 20180723 | 2018-07-23 11:49:11.754000+0000 |        samb | M266
       MPLS2 | 20180723 | 2018-07-23 12:01:18.163000+0000 |     sandrak | M266
       MPLS2 | 20180723 | 2018-07-23 12:04:22.432000+0000 |      aaronp | M266
       MPLS2 | 20180723 | 2018-07-23 12:08:24.682000+0000 |       johno | M261
       MPLS2 | 20180723 | 2018-07-23 12:17:38.268000+0000 |       jeffb | M266
       MPLS2 | 20180723 | 2018-07-23 12:55:45.911000+0000 |        tedk | M266
       MPLS2 | 20180723 | 2018-07-23 14:04:59.377000+0000 |       tejam | M266

(7 rows)
```

Here are some things to note about the preceding result set:

-   As required by the table's `PRIMARY KEY`, I have filtered
    my `WHERE` clause on the complete partition key
    (`location_id` and `day`)
-   I did not specify the complete PRIMARY KEY, choosing to omit
    `employee_id`
-   The results are sorted by `time_in`, in ascending order; I
    did not specify `ORDER BY`
-   I specified a range on `time_in`, mentioning it twice in
    the `WHERE` clause, instructing Cassandra to return a
    range of data
-   While Cassandra is aware of my system's time zone, the
    `time_in` timestamp is shown in UTC time

As per my clustering key definition, my result set was sorted by the
`time_in` column, with the oldest value at the top.  This is
because, while I did clearly specify my clustering keys, I did not
specify the sort order.  Therefore, it defaulted to ascending order.

Additionally, I omitted the `employee_id` key. I can do that
because I specified the keys that preceded it.  If I opted to skip
`time_in` and specify `employee_id`, this query
would fail. There's more on that later.

So why make `employee_id` part of PRIMARY KEY? It helps to
ensure uniqueness. After all, if two employees came through security at
the exact same time, their writes to the table would conflict. Although
unlikely, designating `employee_id` as the last clustering key
helps to ensure that a last-write-wins scenario does not occur.

Another good question to ask would be, if Cassandra requires specific
keys, how can range query be made to work. Recall that Apache Cassandra
is built on a log-based storage engine (LSM tree). This means that
building a table to return data in the order in which it is written
actually coincides with how Cassandra was designed to work. Cassandra
has problems when it is made to serve random reads but sequential reads
actually work quite well.

Now assume that the requirements change slightly, in that the result set
needs to be in descending order. How can we solve for that? Well, we
could specify an `ORDER BY` clause at query time, but flipping
the sort direction of a large result set can be costly for performance.
What is the best way to solve that? By creating a table designed to
serve that query naturally, of course:

```
CREATE TABLE security_logs_by_location_desc (
  employee_id TEXT,
  time_in TIMESTAMP,
  location_id TEXT,
  day INT,
  mailstop TEXT,
  PRIMARY KEY ((location_id, day), time_in, employee_id))
WITH CLUSTERING ORDER BY (time_in DESC, employee_id ASC);
```

 

 

If I duplicate my data into this table as well, I can run that same
query and get my result set in descending order:

```
INSERT INTO security_logs_by_location_desc (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 9:04:59.377','tejam','M266');
INSERT INTO security_logs_by_location_desc (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 7:17:38.268','jeffb','M266');
INSERT INTO security_logs_by_location_desc (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 7:01:18.163','sandrak','M266');
INSERT INTO security_logs_by_location_desc (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 6:49:11.754','samb','M266');
INSERT INTO security_logs_by_location_desc (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 7:08:24.682','johno','M261');
INSERT INTO security_logs_by_location_desc (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180723,'2018-07-23 7:55:45.911','tedk','M266');

SELECT * FROM security_logs_by_location_desc
WHERE location_id='MPLS2'
AND day=20180723
AND time_in > '2018-07-23 6:00' AND time_in < '2018-07-23 10:00';

 location_id | day      | time_in                         | employee_id | mailstop
-------------+----------+---------------------------------+-------------+----------
       MPLS2 | 20180723 | 2018-07-23 14:04:59.377000+0000 |       tejam | M266
       MPLS2 | 20180723 | 2018-07-23 12:55:45.911000+0000 |        tedk | M266
       MPLS2 | 20180723 | 2018-07-23 12:17:38.268000+0000 |       jeffb | M266
       MPLS2 | 20180723 | 2018-07-23 12:08:24.682000+0000 |       johno | M261
       MPLS2 | 20180723 | 2018-07-23 12:04:22.432000+0000 |      aaronp | M266
       MPLS2 | 20180723 | 2018-07-23 12:01:18.163000+0000 |     sandrak | M266
       MPLS2 | 20180723 | 2018-07-23 11:49:11.754000+0000 |        samb | M266

(7 rows)
```

 

In this way, it is clear how picking the right clustering keys (and sort
direction) also plays a part in designing tables that will perform well
at scale.

### Querying data

While Apache Cassandra is known for its restrictive query model (design
your tables to suit your queries), the previous content has shown that
CQL can still be quite powerful. Consider the following table:

```
CREATE TABLE query_test (
 pk1 TEXT,
 pk2 TEXT,
 ck3 TEXT,
 ck4 TEXT,
 c5 TEXT,
 PRIMARY KEY ((pk1,pk2), ck3, ck4))
WITH CLUSTERING ORDER BY (ck3 DESC, ck4 ASC);

INSERT INTO query_test (pk1,pk2,ck3,ck4,c5) VALUES ('a','b','c1','d1','e1');
INSERT INTO query_test (pk1,pk2,ck3,ck4,c5) VALUES ('a','b','c2','d2','e2');
INSERT INTO query_test (pk1,pk2,ck3,ck4,c5) VALUES ('a','b','c2','d3','e3');
INSERT INTO query_test (pk1,pk2,ck3,ck4,c5) VALUES ('a','b','c2','d4','e4');
INSERT INTO query_test (pk1,pk2,ck3,ck4,c5) VALUES ('a','b','c3','d5','e5');
INSERT INTO query_test (pk1,pk2,ck3,ck4,c5) VALUES ('f','b','c3','d5','e5');
```

Let's start by querying everything for `pk1`:

```
SELECT * FROM query_test WHERE pk1='a';

InvalidRequest: Error from server: code=2200 [Invalid query] message="Cannot execute this query as it might involve data filtering and thus may have unpredictable performance. If you want to execute this query despite the performance unpredictability, use ALLOW FILTERING"
```

 

So what happened here? Cassandra is essentially informing us that it
cannot ensure that this query will be served by a single node. This is
because we have defined `pk1` and `pk2` as a
composite partition key. Without both `pk1` and
`pk2` specified, a single node containing the requested data
cannot be ascertained. However, it does say the following:

```
If you want to execute this query despite the performance unpredictability, use ALLOW FILTERING
```

So let's give that a try:

```
SELECT * FROM query_test
WHERE pk1='a' ALLOW FILTERING;

 pk1 | pk2 | ck3 | ck4 | c5
-----+-----+-----+-----+----
   a |   b |  c3 |  d5 | e5
   a |   b |  c2 |  d2 | e2
   a |   b |  c2 |  d3 | e3
   a |   b |  c2 |  d4 | e4
   a |   b |  c1 |  d1 | e1

(5 rows)
```

That worked. But the bigger question is why? The
`ALLOW FILTERING` directive tells Cassandra that it should
perform an exhaustive seek of all partitions, looking for data that
might match. With a total of six rows in the table, served by a single
node cluster, that will still run fast. But in a multi-node cluster,
with millions of other rows, that query will likely time out.

So, let's try that query again, and this time we'll specify the complete
partition key, as well as the first clustering key:

```
SELECT * FROM query_test
WHERE pk1='a' AND pk2='b' AND ck3='c2';

 pk1 | pk2 | ck3 | ck4 | c5
-----+-----+-----+-----+----
   a |   b |  c2 |  d2 | e2
   a |   b |  c2 |  d3 | e3
   a |   b |  c2 |  d4 | e4

(3 rows)
```

 

That works. So what if we just want to query for a specific
`ck4`, but we don't know which `ck3` it's under?
Let's try skipping `ck3`:

```
SELECT * FROM query_test
WHERE pk1='a' AND pk2='b' AND ck4='d2';

InvalidRequest: Error from server: code=2200 [Invalid query] message="PRIMARY KEY column "ck4" cannot be restricted as preceding column "ck3" is not restricted"
```

Remember, components of the `PRIMARY KEY` definition can be
omitted, as long as (some of) the preceding keys are specified. But they
can only be omitted in order. You can't pick and choose which ones to
leave out.

So how do we solve this issue? Let's use `ALLOW FILTERING`:

```
SELECT * FROM query_test
WHERE pk1='a' AND pk2='b' AND ck4='d2' ALLOW FILTERING;

 pk1 | pk2 | ck3 | ck4 | c5
-----+-----+-----+-----+----
   a |   b |  c2 |  d2 | e2

(1 rows)
```

That works. But given what we know about the `ALLOW FILTERING`
directive, is this OK to do? The answer to this question lies in the
fact that we have indeed specified the complete partition key. By doing
that, Cassandra knows which node can serve the query. While this may not
follow the advice of *build your tables to support your queries*, it may
actually perform well (depending on the size of the result set).

### Note

Avoid using `ALLOW FILTERING`. It might make certain ad-hoc
queries work, but improper use of it may cause your nodes to work too
hard, and whichever is chosen as the coordinator may crash. Definitely
do not deploy any production code that regularly uses CQL queries
containing the `ALLOW FILTERING` directive.

For a quick detour, what if I wanted to know what time it was on my
Apache Cassandra cluster? I could query my table using the
`now()` function:

```
SELECT now() FROM query_test;

 system.now()
--------------------------------------
f83015b0-8fba-11e8-91d4-a7c67cc60e89
f83015b1-8fba-11e8-91d4-a7c67cc60e89
f83015b2-8fba-11e8-91d4-a7c67cc60e89
f83015b3-8fba-11e8-91d4-a7c67cc60e89
f83015b4-8fba-11e8-91d4-a7c67cc60e89
f83015b5-8fba-11e8-91d4-a7c67cc60e89

(6 rows)
```

What happened here? The `now()` function was invoked for each
row in the table. First of all, this is an unbound query and will hit
multiple nodes for data that it's not even using. Secondly, we just need
one result. And third, returning the current time
as `TIMEUUID` isn't very easy to read.

Let's solve problems one and two by changing the table we're querying.
Let's try that on the `system.local` table:

```
SELECT now() FROM system.local ;

 system.now()
--------------------------------------
 94a88ad0-8fbb-11e8-91d4-a7c67cc60e89

(1 rows)
```

The `system.local` table is unique to each node in a Cassandra
cluster. Also, it only ever has one row in it. So, this query will be
served by one node, and there will only be one row returned. But how can
we make that more easier to read? We can use the `dateof()`
function for this:

```
SELECT dateof(now()) FROM system.local;

 system.dateof(system.now())
---------------------------------
 2018-07-25 03:37:08.045000+0000

(1 rows)
```

 

Cassandra has other built-in functions that can help to solve other
problems. We will cover those later.

### Note

You can execute
`SELECT CAST(now() as TIMESTAMP) FROM system.local;` to
achieve the same result.

#### The IN operator

So we've seen that CQL has an `AND` keyword for specifying
multiple filters in the `WHERE` clause. Does it also have an
`OR` keyword, like SQL?

No, it does not. This is because Apache Cassandra is designed to serve
sequential reads, not random reads. It works best when its queries give
it a clear, precise path to the requested data. Allowing filters in the
`WHERE` clause to be specified on an `OR` basis
would force Cassandra to perform random reads, which really works
against how it was built.

However, queries can be made to perform similarly to `OR`, via
the `IN` operator:

```
SELECT * FROM query_test WHERE pk1='a' AND pk2 IN ('b','c');
```

While this query technically will work, its use is considered to be an
anti-pattern in Cassandra. This is because it is a multi-key query,
meaning the primary key filters are filtering on more than one key
value. In this case, Cassandra cannot figure out which node the
requested data is on. We are only giving it one part of the partition
key. This means that it will have to designate one node as a coordinator
node, and then scan each node to build the result set:

```
SELECT * FROM query_test WHERE pk1='a' AND  pk2='b' AND ck3 IN ('c1','c3');
```

This query is also a multi-key query. But, this query will perform
better, because we are at least specifying a complete partition key.
This way, a token-aware application will not require a coordinator node,
and will be able to go directly to the one node that can serve this
request.

Do note that, if you use `IN`, the same restrictions apply as
for other operators. You cannot skip primary keys, and if you use
`IN` on a key, you must do the following:

-   Specify all of the keys prior to it
-   Use `IN` only on the last key specified in the query

 

### Note

Like its `ALLOW FILTERING` counterpart, `IN` queries
can still be served by one node if the complete partition key is
specified. However, it’s a good idea to limit the number of values
specified with the `IN` operator to less than 10.

### Writing data

Given the ways in which Apache Cassandra has been shown to handle things
such as `INSERT`, `UPDATE`, and `DELETE`,
it is important to discuss what they have in common. They all result in
writes to the database. Let's take a look at how each one behaves in
certain scenarios. Assume that we need to keep track of statuses for
orders from an e-commerce website. Consider the following table:

```
CREATE TABLE order_status (
 status TEXT,
 order_id UUID,
 shipping_weight_kg DECIMAL,
 total DECIMAL,
 PRIMARY KEY (status,order_id))
WITH CLUSTERING ORDER BY (order_id DESC);
```

### Note

The `order_status` table is for example purposes only, and is
intended to be used to show how writes work in Apache Cassandra. I do
not recommend building an order-status-tracking system this way.

#### Inserting data

Let's write some data to that table.  To do this, we'll use the
`INSERT` statement.  With an `INSERT` statement, all
`PRIMARY KEY` components must be specified; we will
specify`status` and `order_id`.  Additionally, every
column that you wish to provide a value for must be specified in a
parenthesis list, followed by the`VALUES`in their own
parenthesis list:

```
INSERT INTO order_status (status,order_id,total) VALUES ('PENDING',UUID(),114.22);
INSERT INTO order_status (status,order_id,total) VALUES ('PENDING',UUID(),33.12);
INSERT INTO order_status (status,order_id,total) VALUES ('PENDING',UUID(),86.63);
INSERT INTO order_status (status,order_id,total,shipping_weight_kg)
  VALUES ('PICKED',UUID(),303.11,2);
INSERT INTO order_status (status,order_id,total,shipping_weight_kg)
  VALUES ('SHIPPED',UUID(),218.99,1.05);
INSERT INTO order_status (status,order_id,total,shipping_weight_kg)
  VALUES ('SHIPPED',UUID(),177.08,1.2);
```

### Note

If you're going to need a unique identifier for things such as IDs,
the `UUID()` and `TIMEUUID()` functions can be
invoked in-line as a part of `INSERT`.

As you can see, not all columns need to be specified. In our business
case, assume that we do not know the shipping weight until the order has
been `PICKED`. If I query for all orders currently in a
`PENDING` status, it shows `shipping_weight_kg` as
`null`:

```
SELECT * FROM order_status WHERE status='PENDING';

 status  | order_id                             | shipping_weight_kg | total
---------+--------------------------------------+--------------------+--------
 PENDING | fcb15fc2-feaa-4ba9-a3c6-899d1107cce9 |               null | 114.22
 PENDING | ede8af04-cc66-4b3a-a672-ab1abed64c21 |               null | 86.63
 PENDING | 1da6aef1-bd1e-4222-af01-19d2ab0d8151 |               null | 33.12

(3 rows)
```

Remember, Apache Cassandra does not use `null` in the same way
that other databases may. In the case of Cassandra,
`null` simply means that the currently-requested column does
not contain a value.

### Note

Do not literally `INSERT` a null value into a table. Cassandra
treats this as a `DELETE`, and writes a tombstone. It's also
important to make sure that your application code is also not writing
nulls for column values that are not set.

 

 

#### Updating data

So now let's update one of our `PENDING` orders to a status of
`PICKED`, and give it a value for shipping weight. We can
start by updating our `shipping_weight_kg` for order
`fcb15fc2-feaa-4ba9-a3c6-899d1107cce9`, and we'll assume that
it is `1.4` kilograms. This can be done in two different
ways. Updates and inserts are treated the same in Cassandra, so we could
actually update our row with the `INSERT` statement:

```
INSERT INTO order_status (status,order_id,shipping_weight_kg)
  VALUES ('PENDING',fcb15fc2-feaa-4ba9-a3c6-899d1107cce9,1.4);
```

Or, we can also use the `UPDATE` statement that we know from
SQL:

```
UPDATE order_status SET shipping_weight_kg=1.4
WHERE status='PENDING'
AND order_id=fcb15fc2-feaa-4ba9-a3c6-899d1107cce9;
```

Either way, we can then query our row and see this result:

```
SELECT * FROM order_status
WHERE status='PENDING'
AND order_id=fcb15fc2-feaa-4ba9-a3c6-899d1107cce9;

 status  | order_id                             | shipping_weight_kg | total
---------+--------------------------------------+--------------------+--------
 PENDING | fcb15fc2-feaa-4ba9-a3c6-899d1107cce9 |                1.4 | 114.22

(1 rows)
```

Ok, so now how do we set the `PENDING` status to
`PICKED`? Let's start by trying to `UPDATE` it, as
we would in SQL:

```
UPDATE order_status SET status='PICKED'
WHERE order_id='fcb15fc2-feaa-4ba9-a3c6-899d1107cce9';

InvalidRequest: Error from server: code=2200 [Invalid query] message="PRIMARY KEY part status found in SET part"
```

 

With the `UPDATE` statement in CQL, all
the `PRIMARY KEY` components are required to be specified in
the `WHERE` clause. So how about we try specifying both
`PRIMARY KEY` components in `WHERE`, and both
columns with values in `SET`:

```
UPDATE order_status SET shipping_weight_kg=1.4,total=114.22
WHERE status='PICKED'
AND order_id=fcb15fc2-feaa-4ba9-a3c6-899d1107cce9;
```

So that doesn't error out, but did it work? To figure that out, let's
run a (bad) query using `ALLOW FILTERING`:

```
SELECT * FROM order_status WHERE order_id=fcb15fc2-feaa-4ba9-a3c6-899d1107cce9 ALLOW FILTERING;

 status  | order_id                             | shipping_weight_kg | total
---------+--------------------------------------+--------------------+--------
 PENDING | fcb15fc2-feaa-4ba9-a3c6-899d1107cce9 |                1.4 | 114.22
  PICKED | fcb15fc2-feaa-4ba9-a3c6-899d1107cce9 |                1.4 | 114.22

(2 rows)
```

So for this order ID, there are now two rows present in our table; not
at all what we really wanted to do. Sure, we now have our order in a
`PICKED` state, but our `PENDING` row is still out
there. Why did this happen?

First of all, with both `INSERT` and `UPDATE` you
must specify all of the `PRIMARY KEY` components or the
operation will fail. Secondly, primary keys are unique in Cassandra.
When used together, they essentially point to the column values we want.
But that also means they cannot be updated. The only way to update a
`PRIMARY KEY` component is to delete and then rewrite it.

### Note

To Cassandra, `INSERT` and `UPDATE` are synonymous.
They behave the same, and can mostly be used interchangeably. They both
write column values to a specific set of unique keys in the table. You
can insert new rows with `UPDATE` and you can update existing
rows with `INSERT`.

 

 

#### Deleting data

While deleting data and its associated implications have been discussed,
there are times when rows or individual column values may need to be
deleted. In our use case, we discussed the difficulties of trying to
work with the primary key on something that needs to be dynamic, such
as `status`. In our case, we have an extra row for our order
that we need to delete:

```
DELETE FROM order_status
WHERE status='PENDING'
AND order_id=fcb15fc2-feaa-4ba9-a3c6-899d1107cce9;
```

As mentioned previously, `DELETE` can also enforce the removal
of individual column values:

```
DELETE shipping_weight_kg FROM order_status
WHERE status='PICKED'
AND order_id=99886f63-f271-459d-b0b1-218c09cd05a2;
```

### Note

Again, take care when using `DELETE`. Deleting creates
tombstones, which can be problematic to both data consistency and query
performance.

Similar to the previous write operations, `DELETE` requires a
complete primary key. But unlike the other write operations, you do not
need to provide all of the clustering keys. In this way, multiple rows
in a partition can be deleted with a single command.

### Lightweight transactions

One difference between the CQL `INSERT` and `UPDATE`
statements is in how they handle lightweight transactions. Lightweight
transactions are essentially a way for Apache Cassandra to enforce a
sequence of read-and-then-write operations to apply conditional writes.

Lightweight transactions are invokable at query time. Apache Cassandra
implements the paxos (consensus algorithm) to enforce concurrent
lightweight transactions on the same sets of data.

### Note

A lightweight transaction in flight will block other lightweight
transactions, but will not stop normal reads and writes from querying or
mutating the same data.

 

In any case, an `INSERT` statement can only check whether a
row does not already exist for the specified the `PRIMARY KEY`
components. If we consider our attempts to insert a new row to set our
order status to `PENDING`, this could have been used:

```
INSERT INTO order_status (status,order_id,shipping_weight_kg
VALUES ('PENDING',fcb15fc2-feaa-4ba9-a3c6-899d1107cce9,1.4)
IF NOT EXISTS;
```

Essentially what is happening here is that Cassandra is performing a
read to verify the existence of a row with the specified keys. If that
row exists, the operation does not proceed, and a response consisting of
applied with a value of `false` (along with the column values
which failed to write) is returned. If it succeeds, an applied value of
`true` is returned.

On the other hand, `UPDATE` allows for more granular control
in terms of lightweight transactions. It allows for the use of both
`IF EXISTS` and `IF NOT EXISTS`. Additionally, it
can determine whether a write should occur based on arbitrary column
values. In our previous example, we could make our update
to `shipping_weight_kg` and order total based on a threshold
for `shipping_weight_kg`:

```
UPDATE order_status SET shipping_weight_kg=1.4,total=114.22
WHERE status='PICKED' AND order_id=fcb15fc2-feaa-4ba9-a3c6-899d1107cce9
IF shipping_weight_kg > 1.0;
```

Deletes can also make use of lightweight transactions, much in the same
way that updates do:

```
DELETE FROM order_status
WHERE status='PENDING'
AND order_id=fcb15fc2-feaa-4ba9-a3c6-899d1107cce9
IF EXISTS;
```

### Note

Lightweight transactions do incur a performance penalty, so use them
sparingly. However using them with `DELETE` is probably the
best use case, as the performance hit is preferable to generating many
needless tombstones.

 

### Executing a BATCH statement

One of the more controversial features of CQL is the `BATCH`
statement. Essentially, this allows for write operations to be grouped
together and applied at once, automatically. Therefore, if one of the
statements should fail, they are all rolled back. A common application
of this is for developers to write the same data to multiple query
tables, keeping them in sync. `BATCH` statements in CQL can be
applied as such:

```
BEGIN BATCH
 INSERT INTO security_logs_by_location (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180726,'2018-07-26 11:45:22.004','robp','M266');
 INSERT INTO security_logs_by_location_desc (location_id,day,time_in,employee_id,mailstop)
 VALUES ('MPLS2',20180726,'2018-07-26 11:45:22.004','robp','M266');
APPLY BATCH;
```

Note that statements in `BATCH` are not guaranteed to be
executed in any particular order. All statements within a batch are
assumed to have been applied at the same time, and so will bear the same
write timestamps.

What makes this functionality controversial is that it bears a
resemblance to a keyword in the RDBMS world, which behaves very
differently. RDBMS developers are encouraged to apply several (sometimes
thousands) of writes in a batch, to apply them all in one network trip,
and gain some performance. With Cassandra, this approach is dangerous,
because batching too many writes together can exacerbate a coordinator
node and potentially cause it to crash.

### Note

`BATCH` was just not designed to apply several updates to the
same table. It was designed to apply one update to several (such as five
or six) tables. This fundamental misunderstanding of the purpose
of `BATCH` can potentially affect cluster availability.

### The expiring cell

Apache Cassandra allows for data in cells to be expired. This is called
setting a TTL. TTLs can be applied at write-time, or they can be
enforced at the table level with a default value. To set a TTL on a row
at write time, utilize the `USING TTL` clause:

```
INSERT INTO query_test (pk1,pk2,ck3,ck4,c5)
VALUES ('f','g','c4','d6','e7')
USING TTL 86400;
```

 

Likewise, TTLs can also be applied with the `UPDATE`
statement:

```
UPDATE query_test
USING TTL 86400
SET c5='e7'
WHERE pk1='f' AND pk2='g' AND ck3='c4' AND ck4='d6';
```

TTLs represent the number of seconds elapsed since write-time.

### Note

One day is 86,400 seconds.

### Altering a keyspace

Changing a keyspace to use a different RF or strategy is a simple matter
of using the `ALTER KEYSPACE` command. Let's assume that we
have created a keyspace called `fenago_test`:

```
CREATE KEYSPACE fenago_test WITH replication = {
  'class': 'SimpleStrategy', 'replication_factor': '1'}
AND durable_writes = true;
```

As it is preferable to use `NetworkTopologyStrategy`, we can
alter that easily:

```
ALTER KEYSPACE fenago_test  WITH replication = { 'class':'NetworkTopologyStrategy',
  'datacenter1': '1'};
```

If, at some point, we want to add our second data center, that command
would look like this:

```
ALTER KEYSPACE fenago_test  WITH replication = { 'class': 'NetworkTopologyStrategy',
 'datacenter1': '1', 'datacenter2': '1'};
```

If we added more nodes to both data centers, and needed to increase the
RF in each, we can simply run this:

```
ALTER KEYSPACE fenago_test  WITH replication = {'class': 'NetworkTopologyStrategy',
 'datacenter1': '3', 'datacenter2': '3'};
```

### Note

Updating an RF on a keyspace does not automatically move data around.
The data will need to be streamed via repair, rebuild, or bootstrap.

### Dropping a keyspace

Removing a keyspace is a simple matter of using the
`DROP KEYSPACE` command:

```
DROP KEYSPACE fenago_test;
```

### Note

Dropping a keyspace does not actually remove the data from disk.

### Altering a table

Tables can be changed with the `ALTER` statement, using it to
add a column:

```
ALTER TABLE query_test ADD c6 TEXT;
```

Or to remove a column:

```
ALTER TABLE query_test DROP c5;
```

### Note

Primary key definitions cannot be changed on a table. To accomplish
this, the table must be recreated.

Table options can also be set or changed with the `ALTER`
statement. For example, this statement updates the default TTL on a
table to one day (in seconds):

```
ALTER TABLE query_test WITH default_time_to_live = 86400;
```

### Truncating a table

To remove all data from a table, you can use the
`TRUNCATE TABLE` command:

```
TRUNCATE TABLE query_test;
```

 

### Dropping a table

Removing a table is a simple matter of using the `DROP TABLE`
command:

```
DROP TABLE query_test;
```

### Note

Try to avoid frequent drops or creates of a table with the same name.
This process has proven to be problematic with Apache Cassandra in the
past. If you need to recreate a table, it’s always a good idea to
`TRUNCATE` it before dropping it. It may be helpful to create
a table with a version number on the end of it
(`query_test_v2`) to prevent this problem from occurring.

#### Truncate versus drop

It's important to note that dropping a table is different from
truncating it. A drop will remove the table from the schema definition,
but the data will remain on-disk. With truncate, the data is removed,
but the schema remains. Truncate is also the only way to clear all data
from a table in a single command, as a CQL delete requires key
parameters.

### Creating an index

Cassandra comes with the ability to apply distributed, secondary indexes
on arbitrary columns in a table. For an application of this, let's look
at a different solution for our `order_status` table. For
starters, we'll add the date/time of the order as a clustering column.
Next, we'll store the total as a `BIGINT` representing the
number of cents (instead of `DECIMAL` for dollars), to ensure
that we maintain our precision accuracy. But the biggest difference is
that, in talking with our business resources, we will discover that
bucketing by week will give us a partition of manageable size:

```
CREATE TABLE order_status_by_week (
   week_bucket bigint,
   order_datetime timestamp,
   order_id uuid,
   shipping_weight_kg decimal,
   status text,
   total bigint,
   PRIMARY KEY (week_bucket, order_datetime, order_id)
) WITH CLUSTERING ORDER BY (order_datetime DESC, order_id ASC)
```

 

Next, we will add similar rows into this table:

```
INSERT INTO order_status_by_week (status,order_id,total,week_bucket,order_datetime)
VALUES ('PENDING',UUID(),11422,20180704,'2018-07-25 15:22:28');
INSERT INTO order_status_by_week (status,order_id,total,week_bucket,order_datetime)
VALUES ('PENDING',UUID(),3312,20180704,'2018-07-27 09:44:18');
INSERT INTO order_status_by_week (status,order_id,total,week_bucket,order_datetime)
VALUES ('PENDING',UUID(),8663,20180704,'2018-07-27 11:33:01');
INSERT INTO order_status_by_week (status,order_id,total,shipping_weight_kg,week_bucket,order_datetime)
VALUES ('PICKED',UUID(),30311,2,20180704,'2018-07-24 16:02:47');
INSERT INTO order_status_by_week (status,order_id,total,shipping_weight_kg,week_bucket,order_datetime)
VALUES ('SHIPPED',UUID(),21899,1.05,20180704,'2018-07-24 13:28:54');
INSERT INTO order_status_by_week (status,order_id,total,shipping_weight_kg,week_bucket,order_datetime)
VALUES ('SHIPPED',UUID(),17708,1.2,20180704,'2018-07-25 08:02:29');
```

Now I can query for orders placed during the fourth week of July, 2018:

```
SELECT * FROM order_status_by_week WHERE week_bucket=20180704;

week_bucket | order_datetime                  | order_id | shipping_weight_kg | status  | total
-------------+---------------------------------+--------------------------------------+--------------------+---------+-------
   20180704 | 2018-07-27 16:33:01.000000+0000 | 02d3af90-f315-41d9-ab59-4c69884925b9 |               null | PENDING | 8663
   20180704 | 2018-07-27 14:44:18.000000+0000 | cb210378-752f-4a6b-bd2c-6d41afd4e614 |               null | PENDING | 3312
   20180704 | 2018-07-25 20:22:28.000000+0000 | 59cf4afa-742c-4448-bd99-45c61660aa64 |               null | PENDING | 11422
   20180704 | 2018-07-25 13:02:29.000000+0000 | c5d111b9-d048-4829-a998-1ca51c107a8e |                1.2 | SHIPPED | 17708
   20180704 | 2018-07-24 21:02:47.000000+0000 | b111d1d3-9e54-481e-858e-b56e38a14b57 |                  2 | PICKED | 30311
   20180704 | 2018-07-24 18:28:54.000000+0000 | c8b3101b-7804-444f-9c4f-65c17ff201f2 |               1.05 | SHIPPED | 21899

(6 rows)
```

This works, but without status as a part of the primary key definition,
how can we query for `PENDING` orders? Here is where we will
add a secondary index to handle this scenario:

```
CREATE INDEX [index_name] ON [keyspace_name.]<table_name>(<column_name>);
```

### Note

You can create an index without a name. Its name will then default to
`[table_name]_[column_name]_idx`.

In the following code block, we will create an index, and then show how
it is used:

```
CREATE INDEX order_status_idx ON order_status_by_week(status);

SELECT week_bucket,order_datetime,order_id,status,total FROM order_status_by_week
 WHERE week_bucket=20180704 AND status='PENDING';

 week_bucket | order_datetime      | order_id                             | status  | total
-------------+---------------------+--------------------------------------+-----------------
    20180704 | 2018-07-27 16:33:01 | 02d3af90-f315-41d9-ab59-4c69884925b9 | PENDING |  8663
    20180704 | 2018-07-27 14:44:18 | cb210378-752f-4a6b-bd2c-6d41afd4e614 | PENDING |  3312
    20180704 | 2018-07-25 20:22:28 | 59cf4afa-742c-4448-bd99-45c61660aa64 | PENDING | 11422

(3 rows)
```

In this way, we can query on a column that has a more dynamic value. The
status of the order can effectively be updated, without having to delete
the entire prior row.

#### Caution with implementing secondary indexes

While secondary indexes seem like a simple solution to add a dynamic
querying capability to a Cassandra model, caution needs to be given when
addressing their use. Effective, high-performing, distributed
database-indexing is a computing problem that has yet to be solved.
Proper, well-defined queries based on primary key definitions are
high-performing within Apache Cassandra, because they take the
underlying storage model into consideration. Secondary indexing actually
works against this principle.

Secondary indexes in Apache Cassandra store data in a hidden table
(behind the scenes) that only contains lookups for data contained on the
current node. Essentially, a secondary index query (which is not also
filtered by a partition key) will need to confer with every node in the
cluster. This can be problematic with large clusters and potentially
lead to query timeouts.

 

### Note

Our preceding example using a secondary index gets around this problem,
because our query is also filtering by its partition key. This forces
the query to limit itself to a single node.

Cardinality is another problem to consider when building a secondary
index in Apache Cassandra. Let's say we created a secondary index on
`order_id`, so that we can pull up an individual order if we
had to. In that scenario, the high cardinality of `order_id`
would essentially mean that we would query every node in the cluster,
just to end up reading one partition from one node.

Author (and DataStax Cassandra MVP) Richard Low accurately explains this
in his article *The Sweet Spot for Cassandra Secondary Indexing*,
when he describes creating an index on a high-cardinality column such as
an email address:

> **This means only one node (plus replicas) store data for a given
> email address but all nodes are queried for each lookup. This is
> wasteful—every node has potentially done a disk seek but we've only
> got back one partition.**

On the flip-side of that coin, consider a secondary index on a
low-cardinality column, such as a Boolean. Now consider that the table
in question has 20,000,000 rows. With an even distribution, both index
entries will each point to 10,000,000 rows. That is far too many to be
querying at once.

We have established that querying with a secondary index in conjunction
with a partition key can perform well. But is there a time when querying
only by a secondary index could be efficient? Once again, Low's article
concludes the following:

> *...the best use case for Cassandra's secondary indexes is when p is
> approximately n; i.e. the number of partitions is about equal to the
> number of nodes. Any fewer partitions and your n index lookups are
> wasted; many more partitions and each node is doing many seeks. In
> practice, this means indexing is most useful for returning tens, maybe
> hundreds of results.*

In conclusion, secondary indexing can help with large solutions at scale
under certain conditions. But when used alone, the trade-off is usually
one of giving up performance in exchange for convenience. The number of
nodes in the cluster, total partition keys, and cardinality of the
column in question must all be taken into consideration.

### Dropping an index

Dropping a secondary index on a table is a simple task:

```
DROP INDEX [index_name]
```

If you do not know the name of the index (or created it without a name),
you can describe the table to find it. Indexes on a table will appear at
the bottom of the definition. Then you can `DROP` it:

```
CREATE INDEX ON query_test(c5);
DESC TABLE query_test ;

CREATE TABLE fenago_ch3.query_test (
   pk1 text,
   pk2 text,
   ck3 text,
   ck4 text,
   c5 text,
   PRIMARY KEY ((pk1, pk2), ck3, ck4)
) WITH CLUSTERING ORDER BY (ck3 DESC, ck4 ASC)
...
   AND speculative_retry = '99PERCENTILE';
CREATE INDEX query_test_c5_idx ON fenago_ch3.query_test (c5);

DROP INDEX query_test_c5_idx ;
```

### Creating a custom data type

Apache Cassandra allows for the creation of custom **user-defined
types** (**UDTs**). UDTs allow for further denormalization of data
within a row. A good example of this is a mailing address for customers.
Assume a simple table:

```
CREATE TABLE customer (
 last_name TEXT,
 first_name TEXT,
 company TEXT,
 PRIMARY KEY (last_name,first_name));
```

 

Now, our customers have mailing addresses. Corporate customers usually
have addresses for multiple things, including billing, shipping,
headquarters, distribution centers, store locations, and data centers.
So how do we track multiple addresses for a single customer? One way to
accomplish this would be to create a collection of a UDT:

```
CREATE TYPE customer_address (
 type TEXT,
 street TEXT,
 city TEXT,
 state TEXT,
 postal_code TEXT,
 country TEXT);
```

Now, let's add the `customer_address` UDT to the table as a
list. This way, a customer can have multiple addresses:

```
ALTER TABLE customer ADD addresses LIST<FROZEN <customer_address>>;
```

### Note

The `FROZEN` types are those that are immutable. They are
written once and cannot be changed, short of rewriting all underlying
properties.

With that in place, let's add a few rows to the table:

```
INSERT INTO customer (last_name,first_name,company,addresses) VALUES ('Washburne','Hoban','Serenity',[{type:'SHIPPING',street:'9843 32nd Place',city:'Charlotte',state:'NC',postal_code:'05601',country:'USA'}]);
INSERT INTO customer (last_name,first_name,company,addresses) VALUES ('Washburne','Zoey','Serenity',[{type:'SHIPPING',street:'9843 32nd Place',city:'Charlotte',state:'NC',postal_code:'05601',country:'USA'},{type:'BILL TO',street:'9800 32nd Place',city:'Charlotte',state:'NC',postal_code:'05601',country:'USA'}]);
INSERT INTO customer (last_name,first_name,company,addresses) VALUES ('Tam','Simon','Persephone General Hospital',[{type:'BILL TO',street:'83595 25th Boulevard',city:'Lawrence',state:'KS',postal_code:'66044',country:'USA'}]);
```

Querying it for Zoey Washburne shows that her company has two addresses:

```
SELECT last_name,first_name,company,addresses FROM customer
WHERE last_name='Washburne' AND first_name='Zoey';

last_name | first_name |  company | addresses
-----------+------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------
Washburne |       Zoey | Serenity |[{type: 'SHIPPING', street: '9843 32nd Place', city: 'Charlotte', state: 'NC', postal_code: '05601', country: 'USA', street2: null}, {type: 'BILL TO', street: '9800 32nd Place', city: 'Charlotte', state: 'NC', postal_code: '05601', country: 'USA', street2: null}]

(1 rows)
```

### Altering a custom type

UDTs can have columns added to them. For instance, some addresses have
two lines, so we can add an `address2` column:

```
ALTER TYPE customer_address ADD address2 TEXT;
```

UDT columns can also be renamed with the `ALTER` command:

```
ALTER TYPE customer_address RENAME address2 TO street2;
```

### Note

Columns within a UDT cannot be removed or dropped, only added or
renamed.

### Dropping a custom type

UDTs can be dropped very easily, just by issuing the `DROP`
command. If we create a simple UDT:

```
CREATE TYPE test_type (value TEXT);
```

 

It can be dropped like this:

```
DROP TYPE test_type;
```

### User management

As of Apache Cassandra 2.2, Cassandra uses a role-based permission
system. CQL can be utilized by a superuser to create and manage roles
within Apache Cassandra. Roles can be general permission designations
assigned to users or they can be users themselves.

### Note

The syntax provided will be for the role security of Apache Cassandra
2.2 and up. The syntax for managing users in prior versions is
different. Thus, these commands will not work. For information on
managing security in earlier versions, please consult the documentation
for the appropriate version.

#### Creating a user and role

This creates a new role called `cassdba` and gives it a password and the ability to log in and
makes it a superuser:

```
CREATE ROLE cassdba WITH PASSWORD='flynnLives' AND LOGIN=true and SUPERUSER=true;
```

We can also create simple roles:

```
CREATE ROLE data_reader;
CREATE ROLE data_test;
```

Creating non-superuser roles looks something like this:

```
CREATE ROLE kyle WITH PASSWORD='bacon' AND LOGIN=true;
CREATE ROLE nate WITH PASSWORD='canada' AND LOGIN=true;
```

#### Altering a user and role

By far, the most common reason for modifying a role is to change the
password. Run following coomand to change the default `cassandra`
password:

```
ALTER ROLE cassandra WITH PASSWORD=dsfawesomethingdfhdfshdlongandindecipherabledfhdfh';
```

 

#### Dropping a user and role

Removing a user or role is done like this:

```
DROP ROLE data_test;
```

#### Granting permissions

Once created, permissions can be granted to roles:

```
GRANT SELECT ON KEYSPACE fenago_test TO data_reader;
GRANT MODIFY ON KEYSPACE fenago_test TO data_reader;
```

Roles can also be granted to other roles:

```
GRANT data_reader TO kyle;
```

More liberal permissions can also be granted:

```
GRANT ALL PERMISSIONS ON KEYSPACE fenago_test TO kyle;
```

#### Revoking permissions

Sometimes a permission granted to a role will need to be removed. This
can be done with the `REVOKE` command:

```
REVOKE MODIFY ON KEYSPACE fenago_test FROM data_reader;
```

### Other CQL commands

CQL has some additional commands and constructs that provide additional
functionality. A few of them bear a resemblance to their similarly-named
SQL counterparts, but may behave differently.

 

 

#### COUNT

CQL allows you to return a count of the number of rows in the result
set. Its syntax is quite similar to that of the `COUNT`
aggregate function in SQL. This query will return the number of rows in
the customer table with the last name `Washburne`:

```
SELECT COUNT(*) FROM fenago_ch3.customer WHERE last_name='Washburne';

 count
-------
    2
(1 rows)
```

The most common usage of this function in SQL was to count the number of
rows in a table with an unbound query. Apache Cassandra allows you to
attempt this, but it does warn you:

```
SELECT COUNT(*) FROM fenago_ch3.customer;

 count
-------
    3
(1 rows)
Warnings :
Aggregation query used without partition key
```

This warning is Cassandra's way of informing you that the query was not
very efficient. As described earlier, unbound queries (queries without
`WHERE` clauses) must communicate with every node in the
cluster. `COUNT` queries are no different, and so these
queries should be avoided.

### Note

cqlsh has a hard limit of 10,000 rows per query, so `COUNT`
queries run from cqlsh on large tables will max out at that number.

 

 

#### DISTINCT

CQL has a construct that intrinsically removes duplicate partition key
entries from a result set, using the `DISTINCT` keyword. It
works in much the same way as its SQL counterpart:

```
SELECT DISTINCT last_name FROM customer;

 last_name
-----------
       Tam
 Washburne
(2 rows)
```

The main difference of `DISTINCT` in CQL is that it only
operates on partition keys and static columns.

### Note

The only time in which `DISTINCT` is useful is when running an
unbound query. This can appear to run efficiently in small numbers
(fewer than 100). Do remember that it still has to reach out to all the
nodes in the cluster.

#### LIMIT

CQL allows the use of the `LIMIT` construct, which enforces a
maximum number of rows for the query to return. This is done by adding
the `LIMIT` keyword on the end of a query, followed by an
integer representing the number of rows to be returned:

```
SELECT * FROM security_logs_by_location LIMIT 1;

 location_id | day      | time_in | employee_id | mailstop
-------------+----------+---------------------+-------------+----------
       MPLS2 | 20180723 | 2018-07-23 11:49:11 |        samb | M266
(1 rows)
```

#### STATIC

Static columns are data that is more dependent on the partition keys
than on the clustering keys. Specifying a column as
`STATIC` ensures that its values are only stored once (with
its partition keys) and not needlessly repeated in storage with the row
data.

A new table can be created with a `STATIC` column like this:

```
CREATE TABLE fenago_ch3.fighter_jets (
 type TEXT PRIMARY KEY,
 nickname TEXT STATIC,
 serial_number BIGINT);
```

Likewise, an existing table can be altered to contain a
`STATIC` column:

```
ALTER TABLE fenago_ch3.users_by_dept ADD department_head TEXT STATIC;
```

Now, we can update data in that column:

```
INSERT INTO fenago_ch3.users_by_dept (department,department_head) VALUES
('Engineering','Richard');
INSERT INTO fenago_ch3.users_by_dept (department,department_head) VALUES ('Marketing','Erlich');
INSERT INTO fenago_ch3.users_by_dept (department,department_head) VALUES ('Finance/HR','Jared');

SELECT department,username,department_head,title FROM fenago_ch3.users_by_dept ;

 department  | username | department_head | title
-------------+----------+-----------------+---------------
 Engineering |   Dinesh |         Richard |      Dev Lead
 Engineering | Gilfoyle |         Richard | Sys Admin/DBA
 Engineering |  Richard |         Richard |           CEO
   Marketing |   Erlich |          Erlich |           CMO
  Finance/HR |    Jared |           Jared |           COO
(5 rows)
```

As shown, `department_head` only changes as
per `department`. This is because `department_head`
is now stored with the partition key.

#### User-defined functions

As of version 3.0, Apache Cassandra allows users to create
**user-defined functions** (**UDFs**). As CQL does not supply much in
the way of extra tools and string utilities found in SQL, some of that
function can be recreated with a UDF. Let's say that we want to query
the current year from a `date` column. The `date`
column will return the complete year, month, and day:

```
SELECT todate(now()) FROM system.local;

 system.todate(system.now())
-----------------------------
                  2018-08-03
(1 rows)
```

To just get the year back, we could handle that in the application code,
or, after enabling user-defined functions in the
`cassandra.yaml` file, we could write a small UDF using the
Java language:

```
CREATE OR REPLACE FUNCTION year (input DATE)
 RETURNS NULL ON NULL INPUT RETURNS TEXT
 LANGUAGE java AS 'return input.toString().substring(0,4);';
```

Now, re-running the preceding query with `todate(now())`
nested inside my new `year()` UDF returns this result:

```
SELECT fenago_ch3.year(todate(now())) FROM system.local;

 fenago_ch3.year(system.todate(system.now()))
---------------------------------------------
                                        2018
(1 rows)
```

### Note

To prevent injection of malicious code, UDFs are disabled by default. To
enable their use, set `enable_user_defined_functions: true` in
`cassandra.yaml`. Remember that changes to that file require
the node to be restarted before they take effect.

### cqlsh commands

It's important to note that the commands described in this section are
part of cqlsh only. They are not part of CQL. Attempts to run these
commands from within the application code will not succeed.

#### CONSISTENCY

By default, cqlsh is set to a consistency level of `ONE`. But
it also allows you to specify a custom consistency level, depending on
what you are trying to do. These different levels can be set with the
`CONSISTENCY` command:

```
CONSISTENCY LOCAL_QUORUM;

SELECT last_name,first_name FROM customer ;

 last_name | first_name
-----------+------------
       Tam |      Simon
 Washburne |      Hoban
 Washburne |       Zoey

(3 rows)
```

On a related note, queries at `CONSISTENCY ALL` force a read
repair to occur. If you find yourself troubleshooting a consistency
issue on a small to mid-sized table (fewer than 20,000 rows), you can
quickly repair it by setting the consistency level to `ALL`
and querying the affected rows.

### Note

Querying at consistency `ALL` and forcing a read repair comes
in handy when facing replication errors on something such as the
`system_auth` tables.

```
CONSISTENCY ALL;
Consistency level set to ALL.

SELECT COUNT(*) FROM system_auth.roles;

 count
-------
    4
(1 rows)

Warnings :
Aggregation query used without partition key
```

#### COPY

The `COPY` command delivered with cqlsh is a powerful tool
that allows you to quickly export and import data. Let's assume that I
wanted to duplicate my `customer` table data into another
query table. I'll start by creating the new table:

```
CREATE TABLE customer_by_company ( last_name text,
  first_name text,
  addresses list<frozen<customer_address>>,
  company text,
  PRIMARY KEY (company,last_name,first_name));
```

 

Next, I will export the contents of my `customer` table using
the `COPY TO` command:

```
COPY customer (company,last_name,first_name,addresses) TO '/home/aploetz/Documents/Fenago/customer.txt' WITH DELIMITER= '|' AND HEADER=true;
Reading options from the command line: {'header': 'true', 'delimiter': '|'}
Using 3 child processes

Starting copy of fenago_ch3.customer with columns [company, last_name, first_name, addresses].
Processed: 3 rows; Rate: 28 rows/s; Avg. rate: 7 rows/s
3 rows exported to 1 files in 0.410 seconds.
```

And finally, I will import that file into a new table using the
`COPY FROM` command:

```
COPY customer_by_company (company,last_name,first_name,addresses) FROM '/home/aploetz/Documents/Fenago/customer.txt' WITH HEADER=true and DELIMITER='|';
Reading options from the command line: {'header': 'true', 'delimiter': '|'}
Using 3 child processes

Starting copy of fenago_ch3.customer_by_company with columns [company, last_name, first_name, addresses].
Processed: 3 rows; Rate: 5 rows/s; Avg. rate: 7 rows/s
3 rows imported from 1 files in 0.413 seconds (0 skipped).
```

Sometimes exporting larger tables will require additional options to be
set, in order to eliminate timeouts and errors. For instance, the
`COPY TO` options of `PAGESIZE` and
`PAGETIMEOUT` control how many rows are read for export at
once and how long each read has before it times out. These options can
help to effectively break up the export operation into smaller chunks,
which may be necessary based on the size and topology of the cluster.

### Note

`COPY` has a bit of a bad reputation, as early versions were
subject to timeouts when exporting large tables. Remember that
the `COPY` tool itself is also subject to the constraints
applied by the Apache Cassandra storage model. This means that exporting
a large table is an expensive operation. That being said, I have managed
to leverage the `PAGESIZE` and `PAGETIMEOUT` options
to successfully export 350,000,000 rows from a 40-node cluster without
timeouts or errors.

 

 

#### DESCRIBE

`DESCRIBE` is a command that can be used to show the
definition(s) for a particular object. Its command structure looks like
this:

```
DESC[RIBE] (KEYSPACE|TABLE|TYPE|INDEX) <object_name>;
```

In putting it to use, you can quickly see that it can be used to view
things such as full table options, keyspace replication, and index
definitions.

### Note

The `DESCRIBE` command can be shortened to `DESC`.

Here, we will demonstrate using the `DESC` command on a table:

```
DESC TYPE customer_address;

CREATE TYPE fenago_ch3.customer_address (
 type text,
 street text,
 city text,
 state text,
 postal_code text,
 country text,
 street2 text
);
```

Likewise, the `DESC` command can be used to describe an
`INDEX`:

```
DESC INDEX order_status_idx;

CREATE INDEX order_status_idx ON fenago_ch3.order_status_by_week (status);
```

#### TRACING

The `TRACING` command is a toggle that allows the tracing
functionality to be turned on:

```
TRACING ON
Now Tracing is enabled

TRACING
Tracing is currently enabled. Use TRACING OFF to disable
```
 

Tracing is useful in that it can show why particular queries may be
running slowly. A tracing report allows you to view things about a
query, such as the following:

-   Nodes contacted
-   Number of SSTables read
-   Number of tombstones encountered
-   How long the query took to run

