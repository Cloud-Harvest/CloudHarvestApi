# Silos

## Introduction
Silos are a fundamental concept in the Harvest API. They are used to organize and store data in a structured manner.
Although the data storage location can be customized, the default silos are hard-coded into the application to provide
a consistent and reliable data storage solution. Silos are defined in the API configuration and are used internally to
do work. They are also retrieved by [CloudHarvestAgents](https://github.com/Cloud-Harvest/CloudHarvestAgent) to do 
various task queueing and reporting operations. 

## Custom Silos
_Custom_ Silos can also be added to the system to provide additional data storage locations. This can be useful for
building TaskChains which collect, store, and report data from different sources. For example, one may create a Custom
Silo to connect to a PostgreSQL database, collect data using TaskChain, store that data in a structured manner, and then
write a report TaskChain to retrieve and display that data. Since the Cloud Harvest team can't know what kind of Custom
Silos you may use, we cannot provide documentation on their configuration. However, we provide the following general guidance:
* Ensure that the database is accessible from the Harvest API / Agent.
* Use the most limited possible permissions for the user connecting to the database.
* Use a secure connection to the database.
* Ensure that the database is properly indexed for the queries you will be running. Use `EXPLAIN` plans (or your engine equivalent) to verify that your queries are efficient.
* Utilize read-only connections where possible to prevent data corruption.

## Table of Contents
- [Silos](#silos)
  - [Introduction](#introduction)
  - [Custom Silos](#custom-silos)
  - [Harvest Silos](#harvest-silos)
  - [Silo Configuration](#silo-configuration)
  - [Read Only vs Read Write Silos](#read-only-vs-read-write-silos)
  - [harvest-core](#harvest-core)
  - [harvest-nodes](#harvest-nodes)
  - [harvest-plugin-aws](#harvest-plugin-aws)
  - [harvest-plugin-azure](#harvest-plugin-azure)
  - [harvest-task-queue](#harvest-task-queue)
  - [harvest-task-results](#harvest-task-results)
  - [harvest-tasks](#harvest-tasks)
  - [harvest-tokens](#harvest-tokens)
  - [harvest-users](#harvest-users)

## Harvest Silos
| Name                   | Engine | Purpose                                                                                   |
|------------------------|--------|-------------------------------------------------------------------------------------------|
| `harvest-core`         | Mongo  | Defines the location of the database used to administer the application and its metadata. |
| `harvest-nodes`        | Redis  | Stores information about Agent and Api instances in the stack.                            |
| `harvest-plugin-aws`   | Mongo  | Where AWS data will live.                                                                 |
| `harvest-plugin-azure` | Mongo  | Where Azure data will live.                                                               |
| `harvest-task-queue`   | Redis  | This shows queued tasks that agents have yet to pick up.                                  |
| `harvest-task-results` | Redis  | Where task executor results are stored.                                                   |
| `harvest-tasks`        | Redis  | This shows active tasks that executors are processing or have recently completed.         |
| `harvest-tokens`       | Redis  | Ephemeral user tokens.                                                                    |
| `harvest-users`        | Mongo  | Defines the location of the Harvest user accounts and their associated privileges.        |

## Silo Configuration
Every Silo uses the same configuration format. The following keys are required for each Silo:

| Key        | Description                                                                                                   |
|------------|---------------------------------------------------------------------------------------------------------------|
| `database` | The name of the database to connect to. This can be a string or an integer, depending on the database engine. |
| `engine`   | The database engine to use. This can be any of the following: `mongodb`, `redis`.                             |
| `host`     | The hostname or IP address of the database server.                                                            |
| `password` | The password to use when connecting to the database.                                                          |
| `port`     | The port number to connect to the database on.                                                                |
| `username` | The username to use when connecting to the database.                                                          |

Additional fields can be provided based on the database engine being used. The available parameters for each engine are:

### Additional Mongo Parameters
| Key           | Description                                               |
|---------------|-----------------------------------------------------------|
| `authSource`  | The database to authenticate against.                     |
| `maxPoolSize` | The maximum number of connections in the connection pool. |
| `minPoolSize` | The minimum number of connections in the connection pool. |

### Additional Redis Parameters
| Key                | Description                                               |
|--------------------|-----------------------------------------------------------|
| `decode_responses` | Whether to decode responses from Redis.                   |
| `max_connections`  | The maximum number of connections in the connection pool. |

### Example
```yaml
silos:
  my-silo-identifier:
    database: db_name
    engine: mysql
    host: my-mysql-host
    password: my-mysql-password
    port: 3306
    username: my-mysql-username
```

## Read Only vs Read Write Silos
Silos do not provide any native read-only or read-write functionality. Instead, deployers are responsible for ensuring
that their Silos are configured correctly. For example, if you want to use a read-only database for a specific report,
you must create a Silo which uses read only endpoints and user credentials. Similarly, if you want to use a read-write
database for a specific report, you must create a Silo which uses read-write endpoints and user credentials. The following
is an example of two custom Silo configurations which go to the same physical resource, but one is read-only and the other
is read-write:

```yaml
silos:
  # Read-Write Silo
  my-silo-identifier:
    database: db_name
    engine: mysql
    host: my-mysql-host
    password: my-mysql-password
    port: 3306
    username: my-mysql-username
    
  # Read-Only Silo targeting the same resource
  my-silo-identifier-ro:
    database: db_name
    engine: mysql
    host: my-mysql-host
    password: my-mysql-read-only-password
    port: 3306
    username: my-mysql-read-only-username
```

## harvest-core
The `harvest-core` silo is essential for the administration of the application. It houses the primary database that 
contains all the metadata and configuration details necessary for the smooth operation of the system. This silo uses 
`MongoDB` as its database engine, ensuring a robust, persistent, and scalable storage solution.

The schema for this Silo is variable based on the collection in question.

## harvest-nodes
The `harvest-nodes` silo is responsible for storing detailed information about the various Agent and API instances 
within the stack. This information is crucial for managing and monitoring the different components of the system. 
`Redis` is used as the database engine for this silo, providing fast and efficient data retrieval.

### Storage Format
| Field   | Format                     | Description                                                                                                                                    |
|---------|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`  | `{node_type}::{node_name}` | The name of the node as stored in Redis. The `node_type` is either `api` or `agent`, and the `node_name` is derrived from the node's hostname. |
| `value` | JSON                       | The JSON object containing the node's metadata.                                                                                                |

### Schema
All Nodes provide the following fields which is used for communication, monitoring, reporting, and diagnostic purposes.
```json
{
  "architecture": "string",
  "ip": "string",
  "heartbeat_seconds": "number",
  "name": "string",
  "os": {
    "ID": "string",
    "NAME": "string",
    "VERSION": "string",
    "VERSION_ID": "string"
  },
  "plugins": ["string"],
  "python": "string",
  "role": "string",
  "start": "string (date-time)",
  "version": "string",
  "last": "string (date-time)",
  "duration": "number"
}
```

### Agent Node Schema
Agent Nodes provide the following additional fields in their `value` JSON object.

```json
{
  "queue": {
    "chain_status": {
      "initialized": "integer",
      "running": "integer",
      "complete": "integer",
      "error": "integer",
      "stopped": "integer",
      "stopping": "integer",
      "terminating": "integer"
    }
  },
  "duration": "float",
  "max_chains": "integer",
  "start_time": "datetime",
  "status": "string",
  "stop_time": "datetime",
  "total_chains_in_queue": "integer"
}
```

## harvest-plugin-aws
The `harvest-plugin-aws` silo is designated for storing data retrieved from AWS (Amazon Web Services). This silo ensures 
that all AWS-specific data is organized and easily accessible. `MongoDB` is the chosen database engine for this silo, 
offering a flexible, persistent, and scalable storage solution.

> This silo is only required if the [AWS Plugin](https://github.com/Cloud-Harvest/CloudHarvestPluginAws) is enabled.

## Schema
The schema for this silo is variable based on the collection in question. Collections are created dynamically based on
the provider's API response. For instance, the response from `ec2.describeInstances` will create a collection named
`ec2_instances` based on the [`describe_instances`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2/client/describe_instances.html) API call.
Conversely, the response from `rds.describeDBInstances` will create a collection named `rds_instances` based on the
[`describe_db_instances`](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds/client/describe_db_instances.html) API call.

In both instances, the schema will be based on the response from the API call. However, all records will have the
`Harvest` key which contains metadata about the record.

## harvest-plugin-azure
Similar to the AWS plugin, the `harvest-plugin-azure` silo is used to store data specific to Azure services. This silo 
helps in managing and retrieving Azure-related information efficiently. `MongoDB` serves as the database engine for this 
silo, providing a reliable, persistent, and scalable storage option.

> This silo is only required if the _planned_ Azure Plugin is enabled.

## harvest-task-queue
The `harvest-task-queue` silo is designed to manage the queue of tasks that agents have yet to pick up. This silo 
ensures that tasks are organized and processed in an orderly manner. `Redis` is used as the database engine for this 
silo, offering quick and efficient task management.

### Storage Format
| Field   | Format                             | Description                                                                                                                                                                                                        |
|---------|------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`  | `{task_priority}::{task_chain_id}` | The name of the node as stored in Redis. The `task_chain_priority` is an integer where smaller numbers are higher priority. `0` is the highest priority. The `task_chain_id` is a `uuid4` represented as a string. |
| `value` | JSON                               | The JSON object containing the node's metadata.                                                                                                                                                                    |

### Schema

In the `harvest-task-queue` silo, each task is represented by a JSON object with the following fields:
```json
{
  "id": "string",
  "priority": "integer",
  "name": "string",
  "category": "string",
  "model": "string",
  "config": "object",
  "created": "string (date-time)"
}
```

The most relevant fiends are `model` and `config`. The `model` field specifies the JSON representation of a TaskChain, 
while the `config` field contains additional values that are passed to the TaskChain, such as User Filters or connection
parameters.

## harvest-task-results
The `harvest-task-results` silo is where the results of task executions are stored. This silo is crucial for tracking 
the outcomes of various tasks performed by the system. `Redis` is the database engine for this silo, providing fast and 
reliable storage for task results.

### Storage Format
| Field   | Format              | Description                                                                                         |
|---------|---------------------|-----------------------------------------------------------------------------------------------------|
| `name`  | `{task_chain_id}`   | The name of the node as stored in Redis. The `task_chain_id` is a `uuid4` represented as a string.  |
| `value` | JSON                | The JSON object containing the node's metadata.                                                     |

### Schema
```json
{
  "id": "string",
  "metadata": "dict",
  "result": "Any"
}
```

The `result` field can be any type of data, depending on the task execution. The `metadata` field contains additional
information about the task execution, such as the start time, end time, and status of the task.

## harvest-tasks
The `harvest-tasks` silo keeps track of active tasks that are currently being processed or have recently been completed 
by executors. This silo helps in monitoring the progress and status of ongoing tasks. `Redis` is used as the database 
engine for this silo, ensuring quick access to task information.

### Schema
```json
{
  "id": "string",
  "current": "integer",
  "duration": "float",
    "counts": {
      "complete": "integer",
      "error": "integer",
      "idle": "integer",
      "initialized": "integer",
      "running": "integer",
      "skipped": "integer",
      "terminating": "integer"
    },
  "end": "string (date-time)",
  "message": "string",
  "percent": "float",
  "status": "string",
  "start": "string (date-time)",
  "total": "integer",
  "updated": "string (date-time)"
}
```

## harvest-tokens
The `harvest-tokens` silo is responsible for storing ephemeral user tokens. These tokens are temporary and are used for 
authentication and authorization purposes. `Redis` serves as the database engine for this silo, offering fast and 
efficient token management.

| Field   | Format   | Description                                     |
|---------|----------|-------------------------------------------------|
| `name`  | `string` | The token's identifier.                         |
| `token` | `string` | The token's value.                              |
| `user`  | `string` | The Harvest username associated with the token. |

### Schema
```json
{
  "name": {
    "token": "string",
    "user": "string"
  }
}
```

> This silo has not been implemented. It is planned for future development.

## harvest-users
The `harvest-users` silo defines the location of the Harvest user accounts and their associated privileges. This silo is 
essential for managing user access and permissions within the system. `MongoDB` is the chosen database engine for this 
silo, providing a secure, persistent, and scalable storage solution for user data.

### Schema
```json
```

> This silo has not been implemented. It is planned for future development.
