# Silos

## harvest-core
The `harvest-core` silo is essential for the administration of the application. It houses the primary database that 
contains all the metadata and configuration details necessary for the smooth operation of the system. This silo uses 
`MongoDB` as its database engine, ensuring a robust, persistent, and scalable storage solution.

### Schema
```json

```

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

### Schema
```json
```

## harvest-users
The `harvest-users` silo defines the location of the Harvest user accounts and their associated privileges. This silo is 
essential for managing user access and permissions within the system. `MongoDB` is the chosen database engine for this 
silo, providing a secure, persistent, and scalable storage solution for user data.

### Schema
```json
```
