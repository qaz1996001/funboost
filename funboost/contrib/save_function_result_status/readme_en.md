# Saving Function Consumption Result Status to MySQL

If users want to save the funboost function consumption result status to MySQL, you can create a table as follows:

If you want to save the funboost consumed function result status to MySQL, you can create a table. For example (using dataset, you can directly save dictionaries with automatic table creation):

```sql
CREATE TABLE funboost_consume_results
(

    _id                       varchar(255) not null,
    `function`                varchar(255) null,
    host_name                 varchar(255) null,
    host_process              varchar(255) null,
    insert_minutes            varchar(255) null,
    insert_time               datetime     null,
    insert_time_str           varchar(255) null,
    publish_time              float        null,
    publish_time_format       varchar(255) null,
    msg_dict                  json         null,
    params                    json         null,
    params_str                varchar(255) null,
    process_id                bigint       null,
    queue_name                varchar(255) null,
    result                    text null,
    run_times                 int          null,
    script_name               varchar(255) null,
    script_name_long          varchar(255) null,
    success                   tinyint(1)   null,
    task_id                   varchar(255) null,
    thread_id                 bigint       null,
    time_cost                 float        null,
    time_end                  float        null,
    time_start                float        null,
    total_thread              int          null,
    utime                     varchar(255) null,
    exception                 mediumtext   null,
    rpc_result_expire_seconds bigint       null,
    exception_type            varchar(255) null,
    exception_msg             text         null,
    rpc_chain_error_msg_dict  text         null,
    run_status                varchar(255) null,

    primary key (_id),
    key idx_insert_time (insert_time),
    key idx_queue_name_insert_time (queue_name, insert_time),
    key idx_params_str (params_str)
)
```
